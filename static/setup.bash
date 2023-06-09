#!/bin/bash

yum update -y
yum install httpd -y
service httpd start
chkconfig httpd on
yum -y install python-pip

wget https://cc-ma04274.appspot.com/static/run.py -P /var/www/cgi-bin
chmod +x /var/www/cgi-bin/run.py

# wget https://cc-ma04274.appspot.com/static/requirements.txt -P /var/www/cgi-bin
# chmod +x /var/www/cgi-bin/requirements.txt

# wget https://cc-ma04274.appspot.com/static/pip.sh -P /var/www/cgi-bin
# chmod +x /var/www/cgi-bin/pip.sh

python3 -m pip install numpy
python3 -m pip install pandas
python3 -m pip install yfinance