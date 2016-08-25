#!/mntdir/apps/python_org/2.7.6/bin/python

#TODO check the code in tonight to fix messages for non EC_COMMIT shelves

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
import logging
from termcolor import colored
from check_smoke import check_smoke_run
from datetime import datetime
import atexit

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

#parser = argparse.ArgumentParser(description = 'script to Sanity check shelves with EC_COMMIT')
#parser.add_argument('--cl', type=str, help='shelved cl', required=True)
#args = parser.parse_args()

if  __name__ == '__main__':
    user = sys.argv[1]
    cl = sys.argv[2]
    userList = ['rakhee.k', 'balachandr.r', 'h.yi', 'm.rajagopala', 'saravana.v', 'eric.tian', 'rajesh.rathi', 'l.rubin', 'linglan.z', 'ravindra.mr', 'praveen.kn', 'chehui.wu']
    if user in userList:
        print "%s is allowed to submit" % user
    else:
        print colored("%s is not allowed to submit", "red")  % user
        sys.exit(1)
