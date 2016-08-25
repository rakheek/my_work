#!/mntdir/apps/python_org/2.7.6/bin/python

import os
import re
import sys
import argparse
from P4 import P4, P4Exception
from pprint import pprint
import ConfigParser
import subprocess
from subprocess import Popen, PIPE
from ConfigParser import SafeConfigParser
from collections import deque
import logging
from datetime import datetime, date, time

#config = ConfigParser.ConfigParser()
config = SafeConfigParser()
if (sys.platform == "win32"):
    configPath = os.path.join('e:', '/', 'EC', 'cad_scripts')
    osType = 'win'
elif (sys.platform == "linux2"):
    configPath = os.path.join('/', 'mntdir', 'common', 'ec_scripts')
    osType = 'linux'
testIni = os.path.join(configPath, 'tests.ini')
configIni = os.path.join(configPath, 'config.ini')
listConfigs = [configIni, testIni]
config.read(listConfigs)

p4=P4()

p4.port = config.get('p4_server', 'P4PORT')
p4.user = config.get('p4_server', 'P4USER')
p4.password = config.get('p4_server', 'P4TICKET')

p4.connect()

parser = argparse.ArgumentParser(description = 'Script to monitor EC queues')
parser.add_argument('--queue_type', type=str, help='hw/sw', required=True)
parser.add_argument('--branch_name', type=str, help='branch_name', required=False, default='main')
parser.add_argument('--test', action='store_true', help='test', default=False)
parser.add_argument('--stat', action='store_true', help='stat', default=False)
args = parser.parse_args()

def get_clStartTime(first_line):
    ecHungFlag = "False"
    l = re.compile('\d+-\d+-\d+\s\d+:\d+:\d+')
    m = l.match(first_line)
    dt_string = m.group()
    dt = datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    time_diff = now - dt
    if (args.stat):
        print "The time the CL was in the queue is %s" % (str(time_diff))
    if (time_diff.total_seconds() > 14400):
        ecHungFlag = "True"
    return ecHungFlag
    
def get_shelveTime(cl):
#    now = datetime.datetime.now()
    if args.test:
        prefDir = os.getcwd()
    else:
        prefDir = "/mntdir/common"
    shelveFile = "%s/%s/%s/%s" % (prefDir, "ec_data", "logs", "trigQueue")
    hw_queue = []
    with open(shelveFile) as ft:
        ft.seek(0)
        content = ft.read().splitlines()
    for line in content:
        time, shelve = line.split(",")
        if (shelve == cl):
            shelveTime = time
    ft.close()
    return shelveTime

def chk_queueStuck():
    queue = args.queue_type
    branch = args.branch_name
    ecFlag = "False"
#    now = datetime.datetime.now()
    if args.test:
        prefDir = os.getcwd()
    else:
        prefDir = "/mntdir/common"
    queue_file = "%s/%s/%s/%s_%s" % (prefDir, "ec_data", branch, "ec_commit", queue)
    hw_queue = []
    with open(queue_file) as f:
#        queueCls = (cl.rstrip('\r\n') for cl in f)
        count = sum(1 for line in f)
        f.seek(0)
        if (count > 0):
            queueCls = f.read().splitlines()[0].split(',')
            for queue in queueCls:
                hw_queue.append(queue)
            if (args.stat):
                print "The queue type is %s" % (args.queue_type)
                print "The %s queue is %s" % (args.queue_type, ",".join(hw_queue))

            queue_logFile = "%s/%s/%s/%s" % (prefDir, "ec_data", branch, "ec.log")
            with open(queue_logFile) as f:
                lines = f.read().splitlines()
            line_list = []
            for line in lines:
                if (len(line.replace(" ", ",").split(",")) < 5):
                    pass
                else:
                    first_cl = line.replace(" ", ",").split(",")[5]
                    line_time = "%s %s" % (line.replace(" ", ",").split(",")[0], line.replace(" ", ",").split(",")[0])
                    if(first_cl == hw_queue[0]):
                        clShelveTime = get_shelveTime(hw_queue[0])
                        if( line_time > clShelveTime):
                            line_list.append(line)
            f.close()

            if (args.stat):
                print "These are the log line"
                print ('\n').join(line_list)
            ecFlag = get_clStartTime(line_list[0])
    return ecFlag

#    pprint(line_list)        

if  __name__ == '__main__':
    ecFlag = chk_queueStuck()
    if (args.stat):
        print "The flag is %s" % ecFlag
    else:
        print ecFlag
#    stuckFlag = check_queueStuck()
#    logFile = "%s/%s/%s" % ("/mntdir/common/ec_data", branch, "ec.log")
#    logging.basicConfig(filename=logFile,filemode='a',level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
#    logging.info("EC_COMMITS:%s %s" % (args.queue_type, " ".join(clListAll)))
#

    p4.disconnect()
