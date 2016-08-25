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

def checkFileSize(cl):
    files = []
    filesize = 524288000
    p4.connect()
    try:
        p4.run_login()
        change = p4.fetch_change(cl)
        user = change['User']
        files_inCl = p4.run_opened("-c", cl)
        cl_string = "%s=%s" % ("@", cl)
        for file in files_inCl:
            if (file['action'] == "delete"):
                next
            else:
                depot_File = file['clientFile']
                p4_fstat = p4.run_fstat("-Ol", cl_string)
                if(int(p4_fstat[0]['fileSize']) > filesize):
                    logging.error("File %s could not be submitted as it is %s in size" % (depot_File,int(p4_fstat[0]['fileSize'])))
                    print colored("The filesize of the %s being checked is greater than %s Bytes." % (depot_File,filesize), "red")
                    logging.error("Trigger failed for %s", cl)
                    sys.exit("Error filesize greater than 500MB")
#        logging.info("Trigger started for checking filesize %s" % cl)
    except P4Exception:
        for e in p4.errors:
            sys.exit(e)

if  __name__ == '__main__':
    cl = sys.argv[1]
    if(len(sys.argv) > 2):
        triggerDir = os.getcwd()
    else:
        triggerDir = "/p4/common/bin/triggers"
    logFile = "%s/%s/%s" % (triggerDir, "logs", "psFileSizeCheck.log")
    logging.basicConfig(filename=logFile,filemode='a',level=logging.DEBUG,format='%(asctime)s %(levelname)s %(message)s')
    logging.info("Trigger started for %s", cl)
    fileSizeChk = checkFileSize(cl)
    logging.info("Trigger passed for %s", cl)

