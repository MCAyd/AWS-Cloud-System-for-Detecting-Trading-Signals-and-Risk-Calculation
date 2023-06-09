#lambda/routes
import secrets
import forms
import time
import yfinance as yf
import pandas as pd
import numpy as np
import json
from flask import Flask, request, render_template, redirect, url_for, session, jsonify, flash
from api.ParallelLambda import ParallelLambda
from api.EMRManager import EMRManager
from api.EMRManager import get_credential
import requests
import botocore
from pathlib import Path
from io import StringIO
import configparser

app = Flask(__name__)
SECRET_KEY = secrets.token_urlsafe(16)
app.config['SECRET_KEY'] = SECRET_KEY

@app.route('/',methods=['GET','POST'])
def auth():
        form = forms.CreditForm(request.form)
        if request.method == "POST":
                if form.validate_on_submit():
                        content = form.content.data
                        if content != '':
                                try:
                                        response = get_credential(form.content.data)
                                        session['cred']= response
                                except ValueError:
                                        flash('Ensure credential format is correct', 'fail')
                                        return redirect(url_for('auth'))

                        if len(session) < 8:
                                session['cred']= get_credential(form.content.data)

                                session['audit_table'] = []
                                session['emrcluster'] = []
                                session['bucketname'] = []
                                session['currentstepid'] = []
                                session['currentstepstatus'] = ''
                                session['conf'] = ''
                                return redirect(url_for('post_service'))
                        else:
                                return redirect(url_for('post_service'))

        return render_template('cred.html', form=form)

@app.route('/config', methods=['GET','POST'])
def post_service():
        if len(session) < 8: #means not authenticated 
                return redirect(url_for('auth'))
  
        import http.client
        form = forms.ConfigurationForm(request.form)
        if request.method == "POST":
                if form.validate_on_submit():
                        user_inputs = request.form

                        c = request.form.get('stock')
                        h = request.form.get('history')
                        p = int(request.form.get('days_past'))

                        if p >= int(h):
                                flash('Profit Check Period cannot be longer than Price History', 'fail')
                                return redirect(url_for('post_service'))

                        stock = yf.Ticker(c)
                        period = str(h) + 'd'
                        data = stock.history(period=period)

                        if str(data)[-2:] == '[]':
                                flash('Make sure you entered a valid stock code', 'fail')
                                return redirect(url_for('post_service'))

                        data['Index'] = [i for i in range(0,len(data))]
                        data_raw = data

                        data['Buy']=0
                        data['Sell']=0
                        data = data[['Open','Close','Buy','Sell']]
                        data_json = data.to_json(orient="values")

                        r = int(request.form.get('resource_number'))
                        d = int(request.form.get('shots'))
                        t = request.form.get('select_signal')
                        s = request.form.get('select_service')

                        if s == 'lambda':
                                config = ParallelLambda(data_json,r,d,t,p)
                                start = time.time() #runtime calculation for AWS lambda function.
                                results = config.getpages()
                                run_time = time.time() - start
                                #using class parallellambda all variables transferred for lambda run.
                                overall = None
                                signal_days = None

                                for i,result in enumerate(results):
                                        result = json.loads(result)
                                        if i == 0: #first variable overall takes the array shape, and first result index values
                                                overall = np.array(result[0])
                                                signal_days = result[1]
                                        else: #then other values added to overall
                                                overall = np.add(overall,(result[0]))

                                #first get past days' close to p_table, then find p days later rate and create f_table
                                p_col = data_raw.loc[data_raw.Index.isin(signal_days), 'Close']
                                f_signal_days = np.add(signal_days,p)
                                f_col = data_raw.loc[data_raw.Index.isin(f_signal_days), 'Close']

                                missings = np.empty(len(p_col)-len(f_col)) #create nan array for where no forward day stock value.
                                missings[:] = np.nan
                                f_values = np.concatenate((f_col.values, missings),axis=0)

                                diff_table = p_col.to_frame()
                                diff_table['ForwardClose'] = f_values

                                overall = overall/r #averaged using resource_number
                                ninetyfives = [point[0] for point in overall]
                                ninetynines = [point[1] for point in overall]
                                diff_table['95% R.V.'] = ninetyfives
                                diff_table['99% R.V.'] = ninetynines

                                if t == "buy": #according to signal, profit/loss calculation changes.
                                        diff_table['Profit/Loss'] = diff_table['ForwardClose'] - diff_table['Close']
                                        total_value = np.sum(diff_table['Profit/Loss'])
                                else:
                                        diff_table['Profit/Loss'] = diff_table['Close'] - diff_table['ForwardClose']
                                        total_value = np.sum(diff_table['Profit/Loss'])

                                labels = [signal for signal in range(0,len(overall))]

                                # all elements required for audit_table appended to the session's "audit_table" variable, and session is modified.
                                audit_element = [c,s,r,h,d,t,p,run_time,np.average(ninetyfives),np.average(ninetynines),total_value]
                                session["audit_table"].append(audit_element)
                                session.modified = True

                                return render_template('chart.html', table=diff_table.to_html(), labels=labels, ninetyfives=ninetyfives, ninetynines=ninetynines)

                        else:   
                                # where EMR is selected 
                                csv_buffer = StringIO()
                                data.to_csv(csv_buffer, header=False)

                                if session['emrcluster'] == []:
                                        session['conf'] = [c,s,r,h,d,t,p]
                                        session.modified = True

                                        try: 
                                                emr_job = EMRManager()
                                                emr_job.create_emrcluster()
                                                if session['bucketname'] == []:
                                                        emr_job.create_bucket()
                                                        emr_job.upload_files(csv_buffer)
                                                        emr_job.create_step(emr_job.emr_id,emr_job.bucket_name,r,d,t,p)
                                                        session["bucketname"].append(emr_job.bucket_name)
                                                else:
                                                        emr_job.reupload_files(session['bucketname'][0],csv_buffer)
                                                        emr_job.create_step(emr_job.emr_id,session['bucketname'][0],r,d,t,p)

                                                session["emrcluster"].append(emr_job.emr_id)
                                                session["currentstepid"].append(emr_job.step_id)
                                                session['currentstepstatus'] = ''
                                                session.modified = True
                                                flash('EMR step is configured successfully. You can check results clicking on "Check Result" below', 'success')

                                        except (botocore.exceptions.NoCredentialsError, botocore.exceptions.ClientError):
                                                session['emrcluster'] = []
                                                session['currentstepid'] = []
                                                session.modified = True
                                                flash('Ensure your AWS credentials are correct/up to date. Requires new credentials.', 'fail')
                                                return redirect(url_for('auth'))
                                else:
                                        if session['currentstepstatus'] in ['COMPLETED', 'FAILED', 'CANCELLED']:
                                                session['conf'] = [c,s,r,h,d,t,p]
                                                session.modified = True
                                                try:
                                                        emr_job = EMRManager()
                                                        emr_job.delete_output(session['bucketname'][0])
                                                        emr_job.reupload_files(session['bucketname'][0],csv_buffer)
                                                        emr_job.create_step(session['emrcluster'][0],session['bucketname'][0],r,d,t,p)

                                                        session['currentstepid'] = []
                                                        session['currentstepstatus'] = ''
                                                        session.modified = True
                                                        session["currentstepid"].append(emr_job.step_id)
                                                        flash('EMR step is configured successfully. You can check results clicking on "Check Result" below', 'success')

                                                except (botocore.exceptions.NoCredentialsError, botocore.exceptions.ClientError):
                                                        session['emrcluster'] = []
                                                        session['currentstepid'] = []
                                                        session.modified = True
                                                        flash('Ensure your AWS credentials are correct/up to date. Check your services on AWS console.', 'fail')
                                                        return redirect(url_for('auth'))
                                        else :
                                                flash('There is EMR step running, wait to be finished', 'fail')
                                                return redirect(url_for('post_service'))


        return render_template('config.html', form=form)

@app.route('/chart', methods=['GET','POST'])
def get_chart():
        if len(session) < 8: #means not authenticated 
                return redirect(url_for('auth'))

        if session['currentstepid'] == []:
                flash('No EMR step running currently', 'fail')
                return redirect(url_for('post_service'))

        if session['currentstepid'] == [] and session['emrcluster'] == []:
                flash('Ensure your AWS credentials are correct/up to date. Requires new credentials.', 'fail')
                return redirect(url_for('auth'))

        emr_result = None
        try:
                emr_job = EMRManager()
                status, run_time = emr_job.check_status(session['emrcluster'][0],session['currentstepid'][0])

                if status == 'COMPLETED':
                        emr_result = emr_job.get_output(session['bucketname'][0])
                        session['currentstepstatus'] = status
                        session.modified = True
                elif status in ['FAILED','CANCELLED']:
                        session['currentstepstatus'] = status
                        session.modified = True                
                        flash('Step ended with status FAILED or CANCELLED, may run a new configuration', 'fail')
                        return redirect(url_for('post_service'))
                else:
                        flash('Results are not ready yet but you may still use Lambda configuration', 'fail')
                        return redirect(url_for('post_service'))

        except (botocore.exceptions.NoCredentialsError, botocore.exceptions.ClientError):
                session['emrcluster'] = []
                session['currentstepid'] = []
                session.modified = True
                flash('Ensure your AWS credentials are correct/up to date. Requires new credentials.', 'fail')
                return redirect(url_for('auth'))

        emr_result_dict = {}
        for line in emr_result.split('\n'):
                parts = line.strip().split() # split on whitespace
                if parts != []:
                        key = parts[0]
                        s95 = parts[1]
                        s99 = parts[2]
                        s95 = float(s95)
                        s99 = float(s99)
                        emr_result_dict[key] = [s95,s99]

        emr_data = pd.DataFrame.from_dict(emr_result_dict, orient='index', columns=['s95', 's99'])
        emr_data.index.name = 'signaldays'

        signal_days = []
        for index in emr_data.index.values:
                signal_days.append(int(index))

        c,s,r,h,d,t,p=session['conf']

        data_raw = emr_job.get_dataset(session['bucketname'][0])
        data_raw['Index'] = [i for i in range(0,len(data_raw))]

        #first get past days' close to p_table, then find p days later rate and create f_table
        p_col = data_raw.loc[data_raw.Index.isin(signal_days), 'Close']
        f_signal_days = np.add(signal_days,p)
        f_col = data_raw.loc[data_raw.Index.isin(f_signal_days), 'Close']

        missings = np.empty(len(p_col)-len(f_col)) #create nan array for where no forward day stock value.
        missings[:] = np.nan
        f_values = np.concatenate((f_col.values, missings),axis=0)

        diff_table = p_col.to_frame()
        diff_table['ForwardClose'] = f_values

        ninetyfives = [point for point in emr_data.s95]
        ninetynines = [point for point in emr_data.s99]
        diff_table['95% R.V.'] = ninetyfives
        diff_table['99% R.V.'] = ninetynines

        if t == "buy": #according to signal, profit/loss calculation changes.
                diff_table['Profit/Loss'] = diff_table['ForwardClose'] - diff_table['Close']
                total_value = np.sum(diff_table['Profit/Loss'])
        else:
                diff_table['Profit/Loss'] = diff_table['Close'] - diff_table['ForwardClose']
                total_value = np.sum(diff_table['Profit/Loss'])

        labels = [signal for signal in range(0,len(emr_data))]

        # all elements required for audit_table appended to the session's "audit_table" variable, and session is modified.
        audit_element = [c,s,r,h,d,t,p,run_time,np.average(ninetyfives),np.average(ninetynines),total_value]
        if audit_element not in session['audit_table']:
                session["audit_table"].append(audit_element)
                session.modified = True

        return render_template('chart.html', table=diff_table.to_html(), labels=labels, ninetyfives=ninetyfives, ninetynines=ninetynines)

@app.route('/audit', methods=['GET'])
def get_audit():
        if len(session) < 8: #means not authenticated 
                return redirect(url_for('auth'))

        if session['audit_table'] == []:
                flash('No record in Audit Table', 'fail')
                return redirect(url_for('post_service'))

        audit_table = pd.DataFrame(data=session["audit_table"], columns = ['StockCode','Service','#Resources','DaysHistory','Shots','Signal','ProfitCheckPeriod','Runtime','95(A)','99(A)','Profit/Loss'])
        return render_template('audit.html', table=audit_table.to_html())

@app.route('/reset', methods=['POST','GET'])
def post_reset():
        if len(session) < 8: #means not authenticated 
                return redirect(url_for('auth'))

        if session['audit_table'] == []:
                flash('No record in Audit Table', 'fail')
                return redirect(url_for('post_service'))

        session['audit_table'] = []
        session.modified = True
        return redirect(url_for('post_service'))

@app.route('/terminate', methods=['POST','GET'])
def post_terminate_services():
        if len(session) < 8: #means not authenticated 
                return redirect(url_for('auth'))

        if session['bucketname'] == []:
                flash('Nothing to terminate', 'fail')
                return redirect(url_for('post_service'))

        try:
                emr_job = EMRManager()
                if session['emrcluster'] == []:
                        emr_job.terminate_services('',session['bucketname'][0])
                else :
                        emr_job.terminate_services(session['emrcluster'][0],session['bucketname'][0])

        except (botocore.exceptions.NoCredentialsError, botocore.exceptions.ClientError):
                session['emrcluster'] = []
                session['currentstepid'] = []
                session.modified = True
                flash('Ensure your AWS credentials are correct/up to date. Requires new credentials.', 'fail')
                return redirect(url_for('auth'))

        session['emrcluster'] = []
        session['bucketname'] = []
        session['currentstepid'] = []
        session['currentstepstatus'] = ''
        session['conf'] = ''
        session.modified = True
        return redirect(url_for('post_service'))

if __name__ == '__main__':
        # Entry point for running on the local machine
        # On GAE, endpoints (e.g. /) would be called.
        # Called as: gunicorn -b :$PORT index:app,
        # host is localhost; port is 8080; this file is index (.py)
        app.run(host='127.0.0.1', port=8080, debug=True)