#!/mntdir/apps/python_org/2.7.6/bin/python

import os
import re
import sys
import argparse
from P4 import P4, P4Exception
from pprint import pprint
import smtplib
from smtplib import SMTPException
from email.mime.text import MIMEText
import ConfigParser
import datetime
import subprocess
from subprocess import Popen, PIPE


config = ConfigParser.ConfigParser()
config.read('config.ini')

p4=P4()

p4.port = 'aplp4:2001'
p4.user = 'p4scripts'
p4.password = 'p4adminuser'

p4.connect()

#parser = argparse.ArgumentParser(description = 'script to get shelved CLs matching description by queue')
#parser.add_argument('--queue_type', type=str, help='hw/sw', required=True)
#args = parser.parse_args()

def saveToFile(num_p4d, ps, mem_data):
    outFile = open('/home/perforce/replica_monitor/p4d_stats.txt', 'a')
    cur_time = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
    p4d_num = "%s,%s\n" % (cur_time, num_p4d)
    print p4d_num
    outFile.write(p4d_num)

def get_stats():
    lines = []
    cmd = 'ssh aplp42 top -b -n 1'
    try:
        proc = subprocess.Popen(cmd, shell=True, stdout=PIPE)
#        for line in iter(proc.stdout.readline, b''):
#            print line,
#        proc = subprocess.call(cmd, shell=True)
        output,err = proc.communicate()
    except:
        e = sys.exc_info()[1]
        print "Error: %s" % e
    for line in output.split('\n'):
        lines.append(line)
    for line in lines:
        if(re.search("Mem:", line)):
            mem_line = line
            print mem_line                    
    p4d_ps = []
    count = 0
    for line in lines:
        count += 1
        if (count < 8):
            pass
        else:
            if(re.search("p4d_1", line)):
                p4d_ps.append(line.rstrip())
    sep = re.compile('[\s]+')
    p4d_count = []
    p4d_data =[]
    for ps in p4d_ps:
        list_ps = sep.split(ps)
        num_items = len(sep.split(ps))
        mem = list_ps[num_items-3]
        cpu = int(list_ps[num_items-4])
        if (cpu > 0):
            p4d_data.append(ps)
            print list_ps[num_items -1], list_ps[num_items-3], list_ps[num_items-4] 
            p4d_count.append(cpu)
    return len(p4d_count), p4d_data, mem_line

if  __name__ == '__main__':
    get_stats()
    num_p4d, ps, mem_data = get_stats()
    saveToFile(num_p4d, ps, mem_data)
    p4.disconnect()
