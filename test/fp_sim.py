#! /usr/bin/env python
import time
import random

from fp_lib import *


if __name__ == '__main__':
    #testing
    while 1:
        job = getNextJob()
        if job:
            if job.finished:
                job.running = True
            else:
                job.finished = True
                job.result = float(random.randrange(100, 100000))/100
            putJob(job)
        
        getJobs()
        time.sleep(2)
