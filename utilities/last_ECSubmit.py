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
import datetime

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
p4.user = "p4scripts"
#p4.password = "/home/ecagent/p4_tickets/p4scripts1"
p4.password = "p4adminuser"

p4.connect()

parser = argparse.ArgumentParser(description = 'Script to monitor EC queues')
parser.add_argument('--queue_type', type=str, help='hw/sw', required=True)
parser.add_argument('--branch_name', type=str, help='branch_name', required=False, default='main')
parser.add_argument('--test', action='store_true', help='test', default=False)
parser.add_argument('--stat', action='store_true', help='stat', default=False)
args = parser.parse_args()

def chk_ecSubmit():
    queue = args.queue_type
    branch = args.branch_name
    now = datetime.datetime.utcnow()
    noSubmitFlag = "False"
    if args.test:
        prefDir = os.getcwd()
    else:
        prefDir = "/mntdir/common"
    queue_file = "%s/%s/%s/%s_%s" % (prefDir, "ec_data", branch, "ec_commit", queue)
    if (queue == "hw"):
        client = "%s%s-%s" % ("ec_sgpu-", branch, "root-local")
    elif (queue == "sw"):
        client = "%s%s-%s" % ("ec_sgpu-sw2_", branch, "root-local")
    else:
        print "Invalid client"
    p4.run_login()
    p4_submit = p4.run("changes", "-s", "submitted", "-c", client, "-m", "1")
    for item in p4_submit:
        lastSubmitTime = datetime.datetime.utcfromtimestamp( int(item['time']))
    print now.weekday()
    if (now.weekday() == 5 or now.weekday() == 6):
        pass
    else:
        time_diff = 14400
        if ((now - lastSubmitTime).total_seconds() > int(time_diff)):
            if (args.stat):
                print "The time diff from last submit in seconds is %s" % (now - lastSubmitTime).total_seconds()
            noSubmitFlag = "True" 
    if (args.stat):
        print "The current UTC time is %s" % now
        print "The time for last submit UTC time was %s" % lastSubmitTime
    return noSubmitFlag

if  __name__ == '__main__':
#    submitFlag = chk_ecSubmit()
    noSubmitFlag = chk_ecSubmit()
    print noSubmitFlag
    if (args.stat):
        print "The flag is %s" % noSubmitFlag
#    else:
#    logFile = "%s/%s/%s" % ("/mntdir/common/ec_data", branch, "ec.log")
#    logging.basicConfig(filename=logFile,filemode='a',level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
#    logging.info("EC_COMMITS:%s %s" % (args.queue_type, " ".join(clListAll)))

    p4.disconnect()
