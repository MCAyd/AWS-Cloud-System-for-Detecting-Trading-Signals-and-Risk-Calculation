import os
import boto3
import base64
from concurrent.futures import ThreadPoolExecutor

os.environ['AWS_SHARED_CREDENTIALS_FILE']='./api/cred'
ec2 = boto3.resource('ec2', region_name='us-east-1')

class EC2Manager:

	def create_instances(R,C,H,D,T,P):
		# Set the user-data we need – use your endpoint
		user_data = f"""#!/bin/bash
					echo export STOCK="{C}" >> /etc/profile
					echo export HISTORY="{H}" >> /etc/profile
					echo export SHOTS="{D}" >> /etc/profile
					echo export SIGNAL="{T}" >> /etc/profile
					echo export PERIOD="{P}" >> /etc/profile

					yum update -y
					yum install httpd -y
					service httpd start
					chkconfig httpd on
					yum -y install python-pip

					python3 -m pip install numpy
					python3 -m pip install pandas==1.3.5
					python3 -m pip install pandas_datareader
					python3 -m pip install lxml
					python3 -m pip install appdirs
					python3 -m pip install frozendict
					python3 -m pip install beautifulsoup4
					python3 -m pip install html5lib
					python3 -m pip install multitasking
					python3 -m pip install -i https://pypi.anaconda.org/ranaroussi/simple yfinance

					wget https://cc-ma04274.appspot.com/static/run.py -P /var/www/cgi-bin
					chmod +x /var/www/cgi-bin/run.py
					/var/www/cgi-bin/run.py >> /tmp/output.txt"""

		instances = ec2.create_instances(
		    ImageId = 'ami-06e46074ae430fba6', # Amzn Lnx 2 AMI – update to latest ID
		    MinCount = R,
		    MaxCount = R,
		    InstanceType = 't2.micro',
		    KeyName = 'cwkeypair', # Make sure you have the named us-east-1kp
		    SecurityGroups=['default1'], # Make sure you have the named SSH
		    UserData=user_data # and user-data
		    )

		instance_ids = [instance.id for instance in instances]

		return instance_ids

	def terminate_instances(instance_ids):
		ec2.instances.filter(InstanceIds=instance_ids).terminate()

	# def get_function_outputs(instance_ids):

	# 	def get_function_output(instance_id):
	# 		instance = ec2.Instance(instance_id)
	# 		response = instance.run_command('/var/www/cgi-bin/run.py')
	# 		return response

	# 	with ThreadPoolExecutor() as executor:
	# 		results = executor.map(get_function_output, instance_ids)

	# 	return results


	# def update_instances(instance_ids,C,H,D,T,P):
	# 	# Set the user-data we need – use your endpoint
	# 	user_data = f"""#!/bin/bash
	# 			    echo export STOCK="{C}" >> /etc/profile
	# 				echo export HISTORY="{H}" >> /etc/profile
	# 				echo export SHOTS="{D}" >> /etc/profile
	# 				echo export SIGNAL="{T}" >> /etc/profile
	# 				echo export PERIOD="{P}" >> /etc/profile"""

	# 	user_bytes = user_data.encode("utf-8")
	# 	user_data = base64.b64encode(user_bytes)

	# 	stopped_instance_ids = []
	# 	running_instance_ids = []
		
	# 	for instance_id in instance_ids:
	# 	    instance = ec2.Instance(instance_id)
	# 	    if instance.state["Name"] == "stopped":
	# 	        stopped_instance_ids.append(instance_id)
	# 	    elif instance.state["Name"] == "running":
	# 	        running_instance_ids.append(instance_id)

	# 	if running_instance_ids:
	# 		ec2.instances.filter(InstanceIds=running_instance_ids).stop()
	# 		ec2.Instance(running_instance_ids[0]).wait_until_stopped()
	# 		for instance_id in running_instance_ids:
	# 			instance = ec2.Instance(instance_id)
	# 			instance.modify_attribute(UserData={'Value': user_data})
	
	# 	for instance_id in stopped_instance_ids:
	# 		instance = ec2.Instance(instance_id)
	# 		instance.modify_attribute(UserData={'Value': user_data})

	# 	ec2.instances.filter(InstanceIds=instance_ids).start()
	# 	ec2.Instance(instance_ids[len(instance_ids)-1]).wait_until_running()
