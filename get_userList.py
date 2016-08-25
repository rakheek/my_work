#!/usr/bin/env python

import os
import re
import sys
import argparse
from pprint import pprint
import ConfigParser
import subprocess
from subprocess import Popen, PIPE
from ConfigParser import SafeConfigParser
from P4Session import P4Session, P4Exception

def get_clUserList(p4, clList):
    clList = clList.replace("\\n", "\n")
    clList = clList.split('\n')
    userList = []

    for cl in clList:
        change = p4.fetch_change(cl)
        user = change['User']
        userList.append(user)

    userList.append('rakhee.k') # FIXME (KS): What's this for?
    return sorted(set(userList))

def get_config(): # FIXME: Maybe refactor get_config into module
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
    parser = argparse.ArgumentParser(description = 'Get shelved CLs matching description by queue')
    parser.add_argument('--queue_type', type=str, help='hw/sw', required=True) # FIXME (KS): --queue_type is not used
    parser.add_argument('--cl', type=str, help='cl list', required=True)
    args = parser.parse_args()

    config = get_config()

    try:
        with P4Session(config) as p4:
            clList = args.cl
            userList = get_clUserList(p4, clList)
            print " ".join(userList)

    except P4Exception as e:
        print(e)

if __name__ == '__main__':
    main()
