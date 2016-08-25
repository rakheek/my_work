#!/usr/bin/env python

import os
import re
import sys
import argparse
from P4 import P4, P4Exception
from pprint import pprint
from ConfigParser import SafeConfigParser
from subprocess import Popen, PIPE
from db_common import *
from P4Session import P4Session
from db_shelvedclSet import CLDB

def cdWsRoot(p4, submitWS):
    try:
        print p4.port
        print p4.user
        clientSpec = p4.run("client", "-o", submitWS)
        for client in clientSpec:
            submitDir = client['Root']
        print submitDir
    except P4Exception, e:
        print "Error : ", e
        sys.exit(e)
    if os.path.exists(submitDir):
        os.chdir(submitDir)
    else:
        sys.exit("submitDir does not exist")
    return submitDir

def getClDesc(p4, cl, submitWS):
    clStatus = ""
    change = p4.fetch_change(cl)
    print "Fetching description for %s" % cl
    clDesc = change['Description']
    if(re.search(r'EC_COMMIT', clDesc)):
        commitFlag = "true"
    else:
        commitFlag = "false"
    if(re.search(r'EC_FAILED', clDesc)):
        clStatus = "failed"
    elif(re.search(r'EC_PASSED', clDesc)):
        clStatus = "passed"

    return commitFlag, clStatus

def changeClDesc(p4, cl, submitWS, changeDescFlag, sub_cl):
    print changeDescFlag
    change = p4.fetch_change(cl)
    print "Changing description for %s" % cl

    cldb = CLDB()

    if(changeDescFlag == "Fail"):
        change._description = change['Description'].replace("EC_COMMIT", "EC_FAILED")
        cldb.update(int(cl),status="EC_FAILED")
        print change['Description']
        p4.format_change(change)
        p4.save_change(change, "-f")
    elif(changeDescFlag == "Pass"):
        change._description = change['Description'].replace("EC_COMMIT", "EC_PASSED")
        cldb.update(int(cl),status="EC_PASSED",generated_cl=sub_cl)
	print "submitted cl : %s"%sub_cl
        print change['Description']
        p4.format_change(change)
        p4.save_change(change, "-f")

def getPasswd(p4, args, cl):
    change = p4.fetch_change(cl)
    print change
    submitUser = change['User']
    shelveClient = change['Client']
    print submitUser
    newStr = "%s %s" % ("EC_verified", args.job_name)

    #TODO: What's newClDesc doing here in getPasswd???

    newClDesc = change['Description'].replace("EC_COMMIT", newStr)
    p4_passwd = p4.run("login", "-p", submitUser).pop()
    print "retrieved passwd for user %s" % submitUser
    return shelveClient, submitUser, p4_passwd, newClDesc

def submitShelve(p4, cl, submitUser, p4_passwd, newClDesc, submitDir, submitWS, jobStatus, serialCL):
# Add ectool subroutine
    files = []
    p42 = P4()
    p42.port = p4.port
    print p42.port
    p42.client = submitWS
    print p42.client
    p42.user = submitUser
    p42.password = p4_passwd
    p42.connect()
    submitted_cl=0
    try:
        p42.run('login', '-s')
        print "Logging into perforce as user %s" % (submitUser)
    except P4Exception, e:
        print "Error : ", e
        sys.exit(e)
    changeDescFlag = "Fail"
    shelveCL = p42.fetch_change(cl)
    if(jobStatus == "failed"):
        changeDescFlag = "Fail"
        print "The CL did not pass build/test. Build FAILED: Rejecting %s" % cl
    elif(jobStatus == "passed"):
        with p42.at_exception_level(P4.RAISE_ERRORS):
            p42.run("revert", "//...")
        print "Unshelving CL %s" % cl
        p4_unshelve = p42.run("unshelve", "-f", "-s", cl)
        print "This is unshelve %s" % p4_unshelve
        with p42.at_exception_level(P4.RAISE_ERRORS):
            p4_resolve = p42.run("resolve", "-ay")
            print p4_resolve
            print "resolving workspace %s" % submitWS
        p4_opened = p42.run("opened")
        print p4_opened
        os.chdir(submitDir)
        changeN = p42.fetch_change()
        changeN._description = "%s" % newClDesc
        result = p42.save_change(changeN).pop(0)
        print result
        changeNum = re.search(r'\d+', result).group()
        print changeNum
        reopen_files = p42.run("reopen", "-c", changeNum, "//...")
        print reopen_files
        p4_describe = p42.run_describe(changeNum)
        print p4_describe
        print os.getcwd()
        try:
            print "submitting CL %s" % changeNum
            submit = p42.run("submit", "-c", changeNum)
            print submit
            submitted_cl = changeNum 
            changeDescFlag = "Pass"
            with p42.at_exception_level(P4.RAISE_ERRORS):
                p42.run("revert", "//...")
        except P4Exception, e:
            print "Error : ", e
            changeDescFlag = "Fail"
            with p42.at_exception_level(P4.RAISE_ERRORS):
                p42.run("revert", "//...")
            changeClDesc(p4, cl, submitWS, changeDescFlag, 0)
            print "SUBMIT FAILED: for %s" % changeNum
#            sys.exit(e)
    else:
        print "do not checkin code as build/tests failed"
    p42.disconnect()
    print changeDescFlag
    return changeDescFlag, submitted_cl



def get_config():
    config = SafeConfigParser()
    configPath = os.path.join('/', 'mntdir', 'common', 'ec_scripts_test')
    configIni = os.path.join(configPath, 'config.ini')
    print configIni
    listConfigs = [configIni]
    config.read(listConfigs)
    return config


def main():
    parser = argparse.ArgumentParser(description = 'script to submit shelved CLs')
    parser.add_argument('--cl_list', type=str, help='cl list', required=True)
    parser.add_argument('--branch', type=str, help='branch', required=True)
    parser.add_argument('--job_name', type=str, help='job_name', required=True)
    parser.add_argument('--job_status', type=str, help='job_status', required=False)
    parser.add_argument('--agent', type=str, help='agent', required=False)
    args = parser.parse_args()

    config = get_config()

    clList = args.cl_list
    agent = args.agent
# replace with client from your client
    submitWS_pref = config.get('p4_server', 'sgpu_submit_client_prefix')
    submitWS = "%s-%s-%s-%s" % (submitWS_pref, args.branch, 'root', agent)
#    submitWS = "ec_submit_ws"
    print submitWS
# Add checkout step from ectool
    jobStatus = args.job_status
    clList = clList.split(",")
    print len(clList)
    if len(clList) == 1:
        serialCL = "True"
    else:
        serialCL = "False"

    try:
        with P4Session(config) as p4:
            submitDir = cdWsRoot(p4, submitWS)
            print submitDir

            for cl in clList:
                commitFlag, clStatus = getClDesc(p4, cl, submitWS)
                if commitFlag == "true":
                    shelveClient, submitUser, p4_passwd, newClDesc = getPasswd(p4, args, cl)
                    changeDescFlag, submitted_cl = submitShelve(p4, cl, submitUser, p4_passwd, newClDesc, submitDir, submitWS, jobStatus, serialCL)
                    if (jobStatus == "passed") or (jobStatus == "failed" and serialCL == "True"):
                        changeClDesc(p4, cl, submitWS, changeDescFlag, submitted_cl)
                elif(commitFlag == "false" and clStatus == "passed"):
                    print "The CL is already committed. Skip step"
                elif(commitFlag == "false" and clStatus == "failed"):
                    print "The CL has failed submit FAILED:"

    except P4Exception as e:
        print(e)


if  __name__ == '__main__':
    main()
