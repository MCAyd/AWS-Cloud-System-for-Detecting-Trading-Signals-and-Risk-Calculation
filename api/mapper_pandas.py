#!/usr/bin/python3
import pandas as pd
import random
import sys
import os
from concurrent.futures import ThreadPoolExecutor

names = ['Open','Close','Buy','Sell']
data = pd.read_csv(sys.stdin, sep=",", names=names)

# parallel = int(os.environ['parallel'])
# shots = int(os.environ['shots'])
# signal = str(os.environ['signal'])
# minhistory = int(os.environ['minhistory'])

parallel = int(sys.argv[1])
shots = int(sys.argv[2])
signal = str(sys.argv[3])
minhistory = int(sys.argv[4])

for i in range(2, len(data)):

    body = 0.01

       # Three Soldiers
    if (data.Close[i] - data.Open[i]) >= body  \
and data.Close[i] > data.Close[i-1]  \
and (data.Close[i-1] - data.Open[i-1]) >= body  \
and data.Close[i-1] > data.Close[i-2]  \
and (data.Close[i-2] - data.Open[i-2]) >= body:
        data.at[data.index[i], 'Buy'] = 1

       # Three Crows
    if (data.Open[i] - data.Close[i]) >= body  \
and data.Close[i] < data.Close[i-1] \
and (data.Open[i-1] - data.Close[i-1]) >= body  \
and data.Close[i-1] < data.Close[i-2]  \
and (data.Open[i-2] - data.Close[i-2]) >= body:
        data.at[data.index[i], 'Sell'] = 1


def map_simulate(id):
	for i in range(minhistory, len(data)):
		if signal == str("buy"):
			if data.Buy[i]==1: # if we’re interested in Buy signals
				mean=data.Close[i-minhistory:i].pct_change(1).mean()
				std=data.Close[i-minhistory:i].pct_change(1).std()
				# generate much larger random number series with same broad characteristics
				simulated = [random.gauss(mean,std) for x in range(shots)]
				# sort and pick 95% and 99%  - not distinguishing long/short risks here
				simulated.sort(reverse=True)
				var95 = simulated[int(len(simulated)*0.95)]
				var99 = simulated[int(len(simulated)*0.99)]

				print(i,"\t", var95, var99) # so you can see what is being produced

		else:
			if data.Sell[i]==1: # if we’re interested in Sell signals
				mean=data.Close[i-minhistory:i].pct_change(1).mean()
				std=data.Close[i-minhistory:i].pct_change(1).std()
				# generate much larger random number series with same broad characteristics
				simulated = [random.gauss(mean,std) for x in range(shots)]
				# sort and pick 95% and 99%  - not distinguishing long/short risks here
				simulated.sort(reverse=True)
				var95 = simulated[int(len(simulated)*0.95)]
				var99 = simulated[int(len(simulated)*0.99)]

				print(i,"\t", var95, var99) # so you can see what is being produced

runs=[value for value in range(parallel)]

with ThreadPoolExecutor() as executor:
	executor.map(map_simulate, runs)