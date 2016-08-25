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
import requests
import json
from subprocess import Popen, PIPE
from ConfigParser import SafeConfigParser
import logging
from termcolor import colored
from check_smoke import check_smoke_run
from datetime import datetime

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

branch = 'main'

if(len(sys.argv) > 2):
    dataDir = os.getcwd()
else:
    dataDir = "%s/%s" % ("/mntdir/common/ec_data", branch)

def get_smoke_data(user, client):

    web_str = "%s/%s" % ("http://apldms:8000/smoke/query/api/get_smoke_test_for_user_last_12_hrs/username", user)

    list_Cl = []
    try:
        response = requests.get(web_str)
        json_data = response.json()
        smoke_dicts = json_data['smoke_tests']
        if (smoke_dicts == []):
            smoke_check = "fail"
        else:
            for dict in smoke_dicts:
                if (len(smoke_dicts) == 1):
                    if (dict['client_name'] == client['Client']):
                        smoke_check = "pass"
                    else:
                        smoke_check = "fail"
                else:
                    if (dict['client_name'] == client['Client']):
                        smoke_check = "pass"
#                    list_Cl.append(dict['last_cl'])
#    if(len(list_Cl) > 0):
#        cl_fromDMS = max(list_Cl)
#        if (dict['client_name'] == client['Client']):
#        else:
#            smoke_check = "fail"
    except requests.exceptions.RequestException as e:
        print e
        smoke_check = "pass"
    return smoke_check

def checkFileConflict(file):
    conflictFlag = "false"
    conflictCl = ""
    conflictUser = ""
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
        user = change['User']
        client = p4.fetch_client(change['Client'])
        root = client['Root']
        logging.info("Trigger started for %s" % cl)
        if os.path.isdir(root):
            logging.info("The client root exists %s" % root)
        if (re.search(r'EC_COMMIT', change['Description'])):
            ecCommitFlag = "true"
            logging.info("Found EC_COMMIT keyword")
            files_inCl = p4.run_opened("-c", cl)
            logging.info("files in cl %s" % files_inCl)
            if(not files_inCl):
                logging.error("Exiting in Trigger as %s has no files" % cl)
                sys.exit("There are no files in the ChangeList")
            else:
                for file in files_inCl:
                    logging.info("The file is %s" % file['clientFile'])
                    p4.client = file['client']
                    if(file['action'] == "add") or (file['action'] == "move/delete"):
                        logging.info("The file is add or move/delete %s" % file['clientFile'])
                        pass
                    else:
                        logging.info("The file in edit is %s" % file['clientFile'])
                        logging.info("The file rev is %s" % file['rev'])
                        rev_inCl = file['rev']
                        p4_fstatFile = p4.run_fstat("-T", "depotFile", file['clientFile'])
                        conflict, conflictCl, conflictUser, hwCls, swCls = checkFileConflict(p4_fstatFile[0]['depotFile'])
                        if(conflict == "true"):
                            logging.error("Exiting the Trigger as there are conflicts with files %s in %s CL in queue" % (p4_fstatFile[0]['depotFile'], conflictCl))
                            print colored("You have conflicting files %s in %s CL from %s user in queue\nPlease wait for it to be submitted\nThe sw Queue is: %s\nThe hw Queue is: %s", "red") % (p4_fstatFile[0]['depotFile'], conflictCl, conflictUser, " ".join(swCls), " ".join(hwCls))
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
    return shelveStatus, ecCommitFlag, user, root, client

if  __name__ == '__main__':
    cl = sys.argv[1]
    if(len(sys.argv) > 2):
        triggerDir = os.getcwd()
    else:
        triggerDir = "/p4/common/bin/triggers"
    logFile = "%s/%s/%s" % (triggerDir, "logs", "check_userShelve.log")
    if(len(sys.argv) > 2):
        queueFile = "%s/%s/%s" % (triggerDir, "logs", "trigQueue")
    else:
        queueFile = "/mntdir/common/ec_data/logs/trigQueue"
    queueFH = open(queueFile, 'a')
    db_script = os.path.join( triggerDir, "db_shelvedclSet.py")
    logging.basicConfig(filename=logFile,filemode='a',level=logging.DEBUG,format='%(asctime)s %(levelname)s %(message)s')
    shelveStatus, ecCommitFlag, user, root, client = getFiles(cl)
    if (shelveStatus == "pass" and ecCommitFlag == "true"):
        retcode = get_smoke_data(user, client)
        retcode = "pass"
        logging.info("Trigger passed %s" % retcode)
        if ( retcode == "pass"):
            logging.info("Trigger Passed for EC_COMMIT CL: %s." % cl)
            queueFH.write("%s,%s\n" % (str(datetime.now()), cl))
            command = [db_script, 'insert', '-c', cl, '-s', 'EC_COMMIT', '-u', user, '-b', branch]
            try:
                proc = subprocess.Popen(command, stdout = subprocess.PIPE)
                out, err = proc.communicate()
                logging.info("The DMS was populated for %s with %s" % (cl, out))
            except OSError as e:
                print e
                pass
            print "EC will be triggered for %s. You will receive a email when build starts" % cl
        elif (retcode == "fail"):
            print colored("%s did not run smoke check on %s in the last 12 hours. Please run smoke check and then shelve", "red") % (user, client['Client'])
            sys.exit(1)
    elif (shelveStatus == "pass" and ecCommitFlag == "false"):
        logging.info("Trigger Passed for %s." % cl)
        print "No EC keyword found in CL %s." % cl
    elif (shelveStatus == "fail"):
        sys.exit(1)
    p4.disconnect()
