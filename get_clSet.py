#!/mntdir/apps/python_org/2.7.6/bin/python

import os
import re
import sys
import argparse
from pprint import pprint
import subprocess
from subprocess import Popen, PIPE
from collections import deque
import logging
from datetime import datetime, timedelta
import ConfigParser
from ConfigParser import SafeConfigParser

from P4Session import P4Session, P4Exception

from db_shelvedclSet import CLDB


def get_shelvedCLs(p4, args, config):
    shelvedChanges = []
    shelvedChangesWithEC = []
    allShelvedChangesWithEC = []
#    shelvedChangesWithEC = deque( maxlen = 5)
    count = 0
#   bundleShelve = config.get('hw', 'bundleShelve')
    descKey = "EC_COMMIT"

    if args.queue_type == "hw":
        bundleShelve = 4
    else:
        bundleShelve = 1
    branch = args.branch_name

    cldb = CLDB()

    if args.queue_type == "hw":
        shelvedChanges = cldb.select(branch)
    else :
        shelvedChanges = cldb.select(branch + ',apl')

    for change in shelvedChanges:
        try :
            descCL = p4.run_describe("-S", change)
            for key1 in descCL:
                if re.search(descKey, key1['desc']):
                    if check_cl_type(p4, args, config, change):
		        if args.queue_type == "sw":	
			      res = re.search(r'EC_BUNDLE_CL\s*:\s*(\d{6})',key1['desc'])
			      if res :
                                 bundle_cl = res.group(1)
 				 if isValidCl(p4, bundle_cl) : 
        			    #print "update db with bundle cl" 
            	    		    cldb.update(change, status="EC_COMMIT", bundled_cl=bundle_cl)

                        allShelvedChangesWithEC.append(change)
                        if (count < bundleShelve):
                            shelvedChangesWithEC.append(change)
                            count += 1
	        else :
                    cldb.update(change,status="EC_COMMIT_REMOVED")
        except P4Exception as e:
	    for x in p4.warnings:
               if x.find("no file") >= 0 or x.find("no such") >=0:
            	    cldb.update(change,status="INVALID")


    return shelvedChangesWithEC, allShelvedChangesWithEC


def isValidCl(p4, cl):
    stat = 0
    try :
        ds = p4.run_describe("-S", cl)
        if re.search("EC_COMMIT", ds[0]['desc']):
	   stat	= 1
        
    except P4Exception as e:
        pass

    return stat

def check_cl_type(p4, args, config, cl):
    # TODO: KS: Refactor these arguments

    # check if cl belongs to hw or sw
    queue = args.queue_type
    branch = args.branch_name
    moduleList = config.get(queue, 'modules')
    prefix = config.get(queue, 'clientPrefix')
    clientPrefix = "%s_%s" % (prefix, branch)
    modList = []
    modList = moduleList.split(" ")

    status = isMapped(p4, modList, clientPrefix, cl)

    if queue == "hw":
        if status and not isMapped(p4, ['sw'], clientPrefix, cl):
            return 1
    else:
        if status and isMapped(p4, ['sw'], clientPrefix, cl):
            return 1
        elif ( branch == "apl" or branch == "main" )   and isMapped(p4, ['apl'], "ec", cl):
            return 1

    return 0

def isMapped(p4, modList, clientPrefix, cl):
    for module in modList:
        client = "%s-%s" % (clientPrefix, module)
        p4.client = client
        cl_string = "%s%s" % ("//...@=", cl)
        output = p4.run("fstat", "-F", "isMapped", cl_string)
        if (output):
            return 1
    return 0

def get_config():
    #config = ConfigParser.ConfigParser()
    #config.read('config.ini')

    config = SafeConfigParser()
    if (sys.platform == "win32"):
        configPath = os.path.join('e:', '/', 'EC', 'cad_scripts')
        osType = 'win'
    elif (sys.platform == "linux2"):
        configPath = os.path.join('/', 'mntdir', 'common', 'ec_scripts_test')
        osType = 'linux'
    testIni = os.path.join(configPath, 'tests.ini')
    configIni = os.path.join(configPath, 'config.ini')
    listConfigs = [configIni, testIni]
    config.read(listConfigs)
    return config

def main():
    parser = argparse.ArgumentParser(description='script to get shelved CLs matching description by queue')
    parser.add_argument('--queue_type', type=str, help='hw/sw', required=True)
    parser.add_argument('--branch_name', type=str, help='branch_name', required=False, default='main')
    parser.add_argument('--all', type=int, help='all', required=False, default=False)
    parser.add_argument('--test', action='store_true', help='test', default=False)
    args = parser.parse_args()
    config = get_config()

    queue = args.queue_type
    branch = args.branch_name

    try:
        with P4Session(config) as p4:
            shelvedChangesWithEC, allShelvedChangesWithEC = get_shelvedCLs(p4, args, config)
            clList = shelvedChangesWithEC
            clListAll = allShelvedChangesWithEC
            print clList
        #    for cl in clList:
        #        print cl
            if(args.all):
               print ",".join(clListAll)
            else:
               print ",".join(clList)
            if(args.test):
                curDir = os.getcwd()
                ecCommitFile = "%s/%s/%s_%s" % (curDir, branch, "ec_commit", queue)
            else:
                ecCommitFile = "/%s/%s/%s/%s/%s_%s" % ("mntdir", "common", "ec_data_test", branch, "ec_commit", queue)
            fh = open(ecCommitFile, "w")
            fh.write(",".join(clListAll))
            if(args.test):
                logFile = "%s/%s/%s" % (curDir, branch, "ec.log")
            else:
                logFile = "%s/%s/%s" % ("/mntdir/common/ec_data_test", branch, "ec.log")
            logging.basicConfig(filename=logFile, filemode='a', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
            logging.info("EC_COMMITS:%s %s" % (args.queue_type, " ".join(clListAll)))

    except P4Exception as e:
        print(e)

if  __name__ == '__main__':
    main()
