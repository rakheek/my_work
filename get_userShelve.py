#!/usr/bin/env python

import os
import sys
import argparse
from ConfigParser import SafeConfigParser
from P4Session import P4Session, P4Exception

def get_config():
    config = SafeConfigParser()
    if (sys.platform == "win32"):
        configPath = os.path.join('e:', '/', 'EC', 'cad_scripts')
    elif (sys.platform == "linux2"):
        configPath = os.path.join('/', 'mntdir', 'common', 'ec_scripts_test')

    testIni = os.path.join(configPath, 'tests.ini')
    configIni = os.path.join(configPath, 'config.ini')
    listConfigs = [configIni, testIni]
    config.read(listConfigs)
    return config

def get_clUserList(p4, clList):
    clList = clList.split(',')
    userList = []
    for cl in clList:
        change = p4.fetch_change(cl)
        #print change
        user = change['User']
        print "%s: %s" % (user, cl)
        userList.append(user)

    userList.append('rakhee.k')
    return set(userList)


def main():
    parser = argparse.ArgumentParser(description='script to get shelved CLs matching description by queue')
    parser.add_argument('--queue_type', type=str, help='hw/sw', required=True)
    parser.add_argument('--cl', type=str, help='cl list', required=True)
    args = parser.parse_args()

    clList = args.cl
    config = get_config()

    try:
        with P4Session(config) as p4:
            get_clUserList(p4, clList)
    except P4Exception as e:
        for e in p4.errors:
            sys.exit(e)

if  __name__ == '__main__':
    main()
