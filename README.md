# AWS-Cloud-System-for-Detecting-Trading-Signals-and-Risk-Calculation
This project is an application that supports
determining the risks of using certain trading signals for a
trading strategy using a so-called Monte Carlo method. It
utilizes Google App Engine to host a Flask application that
accesses AWS configurations and an interface for users to
request results through configuration APIs. The project consists
of two distinct configurations: AWS Lambda and AWS Elastic
MapReduce (EMR) which both are utilized for trading signal
detection and risk calculation. The Lambda configuration
includes a lambda function that processes user requests over
AWS gateway. The EMR configuration operates as an API and
requires AWS credentials, using the boto3 module to provision
and manage essential scalable services. The project offers the
flexibility to use the Lambda configuration in parallel with
EMR, and it is possible to reuse an existing bucket and cluster
for EMR configurations to save time and resources. Finally, a
set of results are presented and discussed in terms of time
efficiency and costs would be involved with running the system.

![alt text](https://github.com/MCAyd/AWS-Cloud-System-for-Detecting-Trading-Signals-and-Risk-Calculation/blob/main/Project_Diagram.png)
