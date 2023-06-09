#/cw/api/ParallelLambda
import time
import http.client
from concurrent.futures import ThreadPoolExecutor
import numpy as np

class ParallelLambda:
    def __init__(self,data,r,d,t,p):
        self.data = data
        self.r = r
        self.d = d
        self.t = t
        self.p = p

    def getpages(self):
        def getpage(id):
            try:
                host = "6xrdhegaij.execute-api.us-east-1.amazonaws.com"
                c = http.client.HTTPSConnection(host)
                json= '{ "data": ' + self.data + ', "shots": ' + str(self.d) + ', "signal": ' + str(t_r) + ', "past": ' + str(self.p) + '}'
                c.request("POST", "/default/cwlambda", json)
                response = c.getresponse()
                data = response.read().decode('utf-8')

            except IOError:
                print('Failed to open ', host) #Is the Lambda address correct?
            return data

        parallel = self.r #resource_number
        runs=[value for value in range(parallel)]
        
        t_r = 0 #t_r = 0 if Sell
        if self.t == "buy":
            t_r = 1 #t_r is 1 if Buy

        with ThreadPoolExecutor() as executor:
            results=executor.map(getpage, runs)

        return results