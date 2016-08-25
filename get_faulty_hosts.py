#!/mntdir/apps/python_org/3.4.3/bin/python

import os
import sys
import subprocess
import psutil
import time
from pprint import pprint
import subprocess
from subprocess import Popen, PIPE

def get_faulty_hosts():
        cmd = "%s+%s" % ("date", '"%T"')
        print(cmd)
        try:
            proc = subprocess.Popen(cmd, shell=True, stdout=PIPE)
            output,err = proc.communicate()
            print(output)
        except:
            print("Error: %s" % e)
    
if __name__ == '__main__':
#    faulty_hosts = get_faulty_hosts()
    get_faulty_hosts()
