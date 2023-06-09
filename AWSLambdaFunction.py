import json
import random
import math
import statistics
# data[['Open','Close','Buy','Sell']] 0 1 2 3
# BUY SIGNAL WHERE SIGNAL=1, SELL SIGNAL WHERE SIGNAL=0


def lambda_handler(event, context):
    data= event['data']
    shots = int(event['shots'])
    signal = int(event['signal'])
    history = int(event['past'])
    
    results = []
    
    # return(data,shots,signal,history)
    
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
            data[i][2] = 1
            #print("Buy at ", data.index[i])
    
          # Three Crows
        if (data[i][0] - data[i][1]) >= body  \
    and data[i][1] < data[i-1][1] \
    and (data[i-1][0] - data[i-1][1]) >= body  \
    and data[i-1][1] < data[i-2][1]  \
    and (data[i-2][0] - data[i-2][1]) >= body:
            data[i][3] = 1
            #print("Sell at ", data.index[i])
    
    # Data now contains signals, so we can pick signals with a minimum amount
    # of historic data, and use shots for the amount of simulated values
    # to be generated based on the mean and standard deviation of the recent history
    signal_days = []
    minhistory = history + 1
    if signal == 1:
        for i in range(minhistory, len(data)):
            if data[i][2]==1: # we’re interested in Buy signals
                signal_days.append(i)
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
                result = [var95,var99]
                
                results.append(result)
    else:
        for i in range(minhistory, len(data)):
            if data[i][3]==1: # we’re interested in Sell signals
                signal_days.append(i)
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
            
                result = [var95,var99]
                
                results.append(result)
                
    overall = [results, signal_days]
    return overall