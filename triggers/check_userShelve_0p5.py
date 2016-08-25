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

#parser = argparse.ArgumentParser(description = 'script to Sanity check shelves with EC_COMMIT')
#parser.add_argument('--cl', type=str, help='shelved cl', required=True)
#args = parser.parse_args()

def checkFileConflict(file):
    conflictFlag = "false"
    conflictCl = ""
    conflictUser = ""
    dataDir = "/mntdir/common/ec_data/main-impl-0p5-dev"
#    dataDir = os.getcwd()
    clList = []
    hwQueue = "%s/%s" % (dataDir, "ec_commit_hw")
    swQueue = "%s/%s" % (dataDir, "ec_commit_sw")
    fhhwCl = open(hwQueue, 'r')
    hwCls = fhhwCl.read()
    hwCls = hwCls.rstrip().split(",")
    fhswCl = open(swQueue, 'r')
    swCls = fhswCl.read()
    swCls = swCls.rstrip().split(",")
    clList = list(set(hwCls + swCls))
    clList = filter(None, clList)
    for cl in clList:
        p4_desc = p4.run_describe("-S", cl)
        if (re.search(r'EC_COMMIT', p4_desc[0]['desc'])):
            user = p4_desc[0]['user']
            depotFiles = p4_desc[0]['depotFile']
            for clFile in depotFiles:
                if (clFile == file):
                    conflictCl = cl
                    conflictFlag = "true"
                    conflictUser = user
    return conflictFlag, conflictCl, conflictUser, hwCls, swCls

def getFiles(cl):
    files = []
    count = 0
    shelveStatus = "pass"
    ecCommitFlag = "false"
    try:
        p4.password = config.get('p4_server', 'P4TICKET')
        p4.run_login()
    except P4Exception:
        for e in p4.errors:
            sys.exit(e) 
    try:
        change = p4.fetch_change(cl)
        logging.info("Trigger started for %s" % cl)
        if (re.search(r'EC_COMMIT', change['Description'])):
            ecCommitFlag = "true"
            files_inCl = p4.run_opened("-c", cl)
            if(not files_inCl):
                logging.error("Exiting in Trigger as %s has no files" % cl)
                sys.exit("There are no files in the ChangeList")
            else:
                for file in files_inCl:
                    p4.client = file['client']
                    if(file['action'] == "add"):
                        logging.info("The file is add %s" % file['clientFile'])
                        pass
                    else:
                        rev_inCl = file['rev']
                        p4_fstatFile = p4.run_fstat("-T", "depotFile", file['clientFile'])
                        conflict, conflictCl, conflictUser, hwCls, swCls = checkFileConflict(p4_fstatFile[0]['depotFile'])
                        if(conflict == "true"):
                            logging.error("Exiting the Trigger as there are conflicts with files %s in %s CL in queue" % (p4_fstatFile[0]['depotFile'], conflictCl))
                            print colored("You have conflicting files %s in %s CL from %s user in queue\nPlease either resolve your changes with the CL or wait for it to be submitted\nThe sw Queue is: %s\nThe hw Queue is: %s", "red") % (p4_fstatFile[0]['depotFile'], conflictCl, conflictUser, " ".join(swCls), " ".join(hwCls))
                            sys.exit(1)
                        else:
                            p4_fstat = p4.run_fstat("-T", "headRev", file['clientFile'])
                            headRev = p4_fstat[0]['headRev']
                            if(rev_inCl == headRev):
                                logging.info("The %s file is at head revision" % (file['clientFile']))
                                print "The %s file is at head revision" % (file['clientFile'])
                            else:
                                logging.error("Your shelve did not go through as %s is at rev %s and not at head revision %s. Please fix and re-shelve" % (file['clientFile'], rev_inCl, headRev))
                                print colored("Your shelve did not go through as %s is at rev %s and not at head revision %s. Please fix and re-shelve", "red") % (file['clientFile'], rev_inCl, headRev)
                                shelveStatus = "fail"

    except P4Exception:
        for e in p4.errors:
            print e 
    return shelveStatus, ecCommitFlag

if  __name__ == '__main__':
    cl = sys.argv[1]
#    triggerDir = os.getcwd()
    triggerDir = "/p4/common/bin/triggers"
    logFile = "%s/%s/%s" % (triggerDir, "logs", "check_userShelve.log")
    logging.basicConfig(filename=logFile,filemode='a',level=logging.DEBUG,format='%(asctime)s %(levelname)s %(message)s')
    shelveStatus, ecCommitFlag = getFiles(cl)
    if (shelveStatus == "pass" and ecCommitFlag == "true"):
        logging.info("Trigger Passed for %s." % cl)
        print "EC will be triggered for %s. You will receive a email when build starts" % cl
    elif (shelveStatus == "pass" and ecCommitFlag == "false"):
        logging.info("Trigger Passed for %s." % cl)
        print "No EC keyword found in CL %s." % cl
    elif (shelveStatus == "fail"):
        sys.exit(1)
    p4.disconnect()
