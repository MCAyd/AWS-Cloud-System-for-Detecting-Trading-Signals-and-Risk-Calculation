import os
import boto3
import botocore
from botocore.exceptions import ClientError
import time
from datetime import datetime
import string, random
import pandas as pd

def get_credential(credential):
	credential_lines = credential.split('\n')
	for line in credential_lines[1:]:
		credential_name, credential_value = line.split('=',1)
		os.environ[credential_name] = credential_value.rstrip()

	access_key = os.environ.get('aws_access_key_id')
	secret_key = os.environ.get('aws_secret_access_key')
	session_token = os.environ.get('aws_session_token')
	aws_credentials = {
    'access_key': access_key,
    'secret_key': secret_key,
    'session_token': session_token
	}
	
	return aws_credentials

class EMRManager:

	def __init__(self, emr_id=None):
		access_key = os.environ.get('aws_access_key_id')
		secret_key = os.environ.get('aws_secret_access_key')
		session_token = os.environ.get('aws_session_token')

		self.s3 = boto3.client('s3', region_name='us-east-1', aws_access_key_id=access_key,
			aws_secret_access_key=secret_key, aws_session_token=session_token)
		self.emr = boto3.client('emr', region_name='us-east-1', aws_access_key_id=access_key,
			aws_secret_access_key=secret_key, aws_session_token=session_token)
		def generate_bucket_name():
			letters = string.ascii_lowercase
			bucket_name = ''.join(random.choice(letters) for i in range(6))
			return bucket_name
		bucket_name = generate_bucket_name()
		self.step_id = ''
		self.bucket_name = bucket_name
		self.emr_id = ''

	def create_bucket(self):
		self.s3.create_bucket(Bucket=self.bucket_name,ObjectOwnership='ObjectWriter')
		self.s3.put_public_access_block(Bucket=self.bucket_name, PublicAccessBlockConfiguration={'BlockPublicAcls': False,'IgnorePublicAcls': False,'BlockPublicPolicy': False,'RestrictPublicBuckets': False})
		self.s3.put_bucket_acl(ACL='public-read-write',Bucket=self.bucket_name)
        
	def upload_files(self,data):
		mapper_path = os.path.join(os.getcwd(), './api/mapper.py')
		reducer_path = os.path.join(os.getcwd(), './api/reducer.py')
		file_name = 'input.txt'
		self.s3.put_object(Body=data.getvalue(), Bucket=self.bucket_name, Key=file_name)
		self.s3.upload_file(mapper_path, self.bucket_name, 'mapper.py')
		self.s3.upload_file(reducer_path, self.bucket_name, 'reducer.py')

	def reupload_files(self,bucket_name, data):
		file_name = 'input.txt'
		self.s3.put_object(Body=data.getvalue(), Bucket=bucket_name, Key=file_name)

	def get_output(self,bucket_name):
		prefix = 'output'
		file_name = 'part-00000'

		response = self.s3.get_object(Bucket=bucket_name, Key=f"{prefix}/{file_name}")
		data = response['Body'].read().decode('utf-8')
		return data

	def get_dataset(self, bucket_name):
	    s3_object = self.s3.get_object(Bucket=bucket_name, Key='input.txt')
	    data = pd.read_csv(s3_object['Body'], index_col=0, names=['Date', 'Open', 'Close', 'Buy', 'Sell'])
	    return data

	def delete_output(self, bucket_name):
		access_key = os.environ.get('aws_access_key_id')
		secret_key = os.environ.get('aws_secret_access_key')
		session_token = os.environ.get('aws_session_token')

		prefix = 'output/'
		s3 = boto3.resource('s3', aws_access_key_id=access_key,
			aws_secret_access_key=secret_key, aws_session_token=session_token)
		bucket = s3.Bucket(bucket_name)
		bucket.objects.filter(Prefix=prefix).delete()

		bucket.Object(prefix).delete()

	def terminate_services(self, emr_id, bucket_name):
		access_key = os.environ.get('aws_access_key_id')
		secret_key = os.environ.get('aws_secret_access_key')
		session_token = os.environ.get('aws_session_token')
		
		try: 
			if emr_id != '':
				self.emr.terminate_job_flows(JobFlowIds=[emr_id])
				time.sleep(30)

			s3 = boto3.resource('s3',aws_access_key_id=access_key,
				aws_secret_access_key=secret_key, aws_session_token=session_token)
			bucket = s3.Bucket(bucket_name)
			for obj in bucket.objects.all():
				obj.delete()
			bucket.delete()

		except (botocore.exceptions.NoCredentialsError, botocore.exceptions.ClientError):
			s3 = boto3.resource('s3',aws_access_key_id=access_key,
			aws_secret_access_key=secret_key, aws_session_token=session_token)
			bucket = s3.Bucket(bucket_name)
			for obj in bucket.objects.all():
				obj.delete()
			bucket.delete()

	def create_emrcluster(self):
		try:	
			response = self.emr.run_job_flow(
						Name="cw-emr-cluster",
						LogUri='s3://' + str(self.bucket_name) + '/my-emr-logs',
						ReleaseLabel='emr-5.36.0',
						Instances={
						'HadoopVersion': '2.10.1',
						'KeepJobFlowAliveWhenNoSteps': True,
						'TerminationProtected': False,
						'InstanceGroups': [
						    {
						        'Name': 'Master',
						        'Market': 'ON_DEMAND',
						        'InstanceRole': 'MASTER',
						        'InstanceType': 'm4.large',
						        'InstanceCount': 1
						    },
						    {
						        'Name': 'Core',
						        'Market': 'ON_DEMAND',
						        'InstanceRole': 'CORE',
						        'InstanceType': 'm4.large',
						        'InstanceCount': 1
						    },
						    {
						        'Name': 'Task',
						        'Market': 'ON_DEMAND',
						        'InstanceRole': 'TASK',
						        'InstanceType': 'm4.xlarge',
						        'InstanceCount': 2,
						    },
						]
						},
						Applications=[
					        {
					            'Name': 'Hive'
					        },
					        {
					            'Name': 'Hue'
					        },
					        {
					            'Name': 'Mahout'
					        },
					    	{
					            'Name': 'Pig'
					        },
					       	{
					            'Name': 'Tez'
					        }
					    ],
						VisibleToAllUsers=True,
						ServiceRole='EMR_DefaultRole',
						JobFlowRole='EMR_EC2_DefaultRole'
						)

			print(f"EMR Cluster created with ID: {response['JobFlowId']}")
			self.emr_id = response['JobFlowId']

		except ClientError as e:
		    print(f"Error creating EMR Cluster: {e}")

	def create_step(self,emr_id,bucket_name,r,d,t,p):
		# S3 bucket path for input and output
		s3_input_path = 's3://' + bucket_name + '/input.txt'
		s3_output_path = 's3://' + bucket_name + '/output/'

		# S3 path for mapper and reducer
		s3_mapper_path = 's3://' + bucket_name + '/mapper.py'
		s3_reducer_path = 's3://' + bucket_name + '/reducer.py'
		files_path = s3_mapper_path + ',' + s3_reducer_path

		# User-defined variables
		parallel = r
		shots = d
		t_r = 0 #t_r = 0 if Sell
		if t == "buy":
			t_r = 1 #t_r is 1 if Buy
		signal = t_r
		minhistory = p

		# Define the streaming step
		streaming_step = {
		    'Name': 'Streaming Step',
		    'ActionOnFailure': 'CONTINUE',
		    'HadoopJarStep': {
		        'Jar': 'command-runner.jar',
		        'Args': [
		            'hadoop-streaming',
		            '-D', 'mapreduce.input.fileinputformat.split.maxsize=100000000', # Max split size
            		'-D', 'mapreduce.input.fileinputformat.split.minsize=100000000', # Min split size
		            '-files', files_path,
		           	'-mapper', 'mapper.py',
		            '-reducer', 'reducer.py',
		           	'-input', s3_input_path,
		           	'-output', s3_output_path,
		           	'-numReduceTasks',str(1),
		            '-cmdenv', 'parallel=' + str(parallel),
		            '-cmdenv', 'shots=' + str(shots),
		            '-cmdenv', 'signal=' + str(signal),
		            '-cmdenv', 'minhistory=' + str(minhistory)
		        ],
		    }
		}

		response = self.emr.add_job_flow_steps(JobFlowId=emr_id, Steps=[streaming_step])
		step_id = response['StepIds'][0]
		self.step_id = step_id

	def check_status(self, emr_id, step_id):
		status = self.emr.describe_step(ClusterId=emr_id, StepId=step_id)['Step']['Status']['State']
		if status == 'COMPLETED':
			start_time = self.emr.describe_step(ClusterId=emr_id, StepId=step_id)['Step']['Status']['Timeline']['StartDateTime']
			end_time = self.emr.describe_step(ClusterId=emr_id, StepId=step_id)['Step']['Status']['Timeline']['EndDateTime']
			run_time = (datetime.fromisoformat(str(end_time)) - datetime.fromisoformat(str(start_time))).total_seconds()
			return status, run_time

		return status, None