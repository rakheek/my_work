#!/mntdir/apps/python_org/3.4.3/bin/python

import os
import sys
import subprocess
import psutil
import time
from pprint import pprint

def get_faulty_hosts():
    with open(lsf_hosts as f):
        hosts = f.readlines()

    for host in hosts:
        print(host)

if __name__ == '__main__':
#    faulty_hosts = get_faulty_hosts()
    get_faulty_hosts()
#                print("process %s with %s by %s is taking %s cputime" % (proc.pid, proc.name(), proc.username(), proc.cpu_percent(interval=1)))
