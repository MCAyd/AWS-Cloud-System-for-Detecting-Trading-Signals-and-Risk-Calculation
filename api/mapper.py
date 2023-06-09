#!/usr/bin/python3
import random
import math
import statistics
import sys
import os
from concurrent.futures import ThreadPoolExecutor

parallel = int(os.environ['parallel'])
shots = int(os.environ['shots'])
signal = int(os.environ['signal'])
minhistory = int(os.environ['minhistory'])

minhistory = minhistory + 1

data = []
for line in sys.stdin:
	line = line.strip()
	values = line.split(",")
	values = [float(values[x]) for x in range(1,len(values))]
	data.append(values)

def pct_change(a):
	pct = [(a[i]-a[i-1])/(a[i-1]) for i in range(1, len(a))]
	pct_mean = statistics.mean(pct)
	pct_std = statistics.stdev(pct)
	return (pct_mean,pct_std)

for i in range(2, len(data)):
	body = 0.01

      # Three Soldiers
	if (data[i][1] - data[i][0]) >= body  \
and data[i][1] > data[i-1][1]  \
and (data[i-1][1] - data[i-1][0]) >= body  \
and data[i-1][1] > data[i-2][1]  \
and (data[i-2][1] - data[i-2][0]) >= body:
		data[i][2] = 1.0

      # Three Crows
	if (data[i][0] - data[i][1]) >= body  \
and data[i][1] < data[i-1][1] \
and (data[i-1][0] - data[i-1][1]) >= body  \
and data[i-1][1] < data[i-2][1]  \
and (data[i-2][0] - data[i-2][1]) >= body:
		data[i][3] = 1.0
     	
# Data now contains signals, so we can pick signals with a minimum amount
# of historic data, and use shots for the amount of simulated values
# to be generated based on the mean and standard deviation of the recent history
def map_simulate(id):
	results = []
	if signal == 1:
		for i in range(minhistory, len(data)):
			if data[i][2]==1.0: # we’re interested in Buy signals
				a = []
				for j in range(i-minhistory,i):
					a.append(data[j][1])
				mean,std=pct_change(a)
				# generate much larger random number series with same broad characteristics
				simulated = [random.gauss(mean,std) for x in range(shots)]
				# sort and pick 95% and 99%  - not distinguishing long/short risks here
				simulated.sort(reverse=True)
				var95 = simulated[int(len(simulated)*0.95)]
				var99 = simulated[int(len(simulated)*0.99)]
				result = [i,var95,var99]

				results.append(result)#so you can see what is being produced
	else:
		for i in range(minhistory, len(data)):
			if data[i][3]==1.0: # we’re interested in Sell signals
				a = []
				for j in range(i-minhistory,i):
					a.append(data[j][1])
				mean,std=pct_change(a)
				# generate much larger random number series with same broad characteristics
				simulated = [random.gauss(mean,std) for x in range(shots)]
				# sort and pick 95% and 99%  - not distinguishing long/short risks here
				simulated.sort(reverse=True)
				var95 = simulated[int(len(simulated)*0.95)]
				var99 = simulated[int(len(simulated)*0.99)]
				result = [i,var95,var99]

				results.append(result)#so you can see what is being produced

	return results

runs=[value for value in range(parallel)]
results = []
with ThreadPoolExecutor() as executor:
	results = executor.map(map_simulate, runs)

for result in results:
	for element in result:
		print(element[0],"\t", element[1], element[2]) # so you can see what is being produced


