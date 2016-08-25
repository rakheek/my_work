#!/mntdir/apps/python_org/3.4.3/bin/python

import os
import sys
import subprocess
import psutil
import time
from pprint import pprint

def find_ps():
     for pid in psutil.pids():
        p = psutil.Process(pid)
        print(p.cpu_percent())
        if(p.cpu_percent() > 30):
            print(p.name())

def poll(interval):
    # sleep some time
    time.sleep(interval)
    procs = []
    procs_status = {}
    for p in psutil.process_iter():
        try:
            p.dict = p.as_dict(['pid', 'username', 'nice', 'memory_info',
                'memory_percent', 'cpu_percent',
                'cpu_times', 'name', 'status'])
            try:
                procs_status[str(p.dict['status'])] += 1
            except KeyError:
                procs_status[str(p.dict['status'])] = 1
        except psutil.NoSuchProcess:
            pass
        else:
            procs.append(p)
            # return processes sorted by CPU percent usage
#    print(procs)
    processes = sorted(procs, key=lambda p: p.dict['cpu_percent'], reverse=True)
    return (processes, procs_status)

if __name__ == '__main__':
    procs, status = poll(5)
#    poll(5)
    pid_list = []
    for proc in procs:
        if (proc.name() != "find_process.py"):
#        if (proc.status() == "running"):
            if(proc.cpu_percent() > 70):
                pid_list.append(proc.pid)
                print("process %s with %s by %s is taking %s cputime" % (proc.pid, proc.name(), proc.username(), proc.cpu_percent(interval=1)))
