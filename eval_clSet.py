#!/usr/bin/env python

import os
import re
import sys
import argparse
from ConfigParser import SafeConfigParser
from P4Session import P4Session, P4Exception

def get_config():
    config = SafeConfigParser()
    if (sys.platform == "win32"):
        configPath = os.path.join('e:', '/', 'EC', 'cad_scripts')
        #osType = 'win'
    elif (sys.platform == "linux2"):
        configPath = os.path.join('/', 'mntdir', 'common', 'ec_scripts_test')
        #osType = 'linux'
    testIni = os.path.join(configPath, 'tests.ini')
    configIni = os.path.join(configPath, 'config.ini')
    listConfigs = [configIni, testIni]
    config.read(listConfigs)
    return config


def get_clUserList(p4, clList):
    clList = clList.replace("\\n", "\n")
    clList = clList.split('\n')
    refinedList = []
    for cl in clList:
        change = p4.fetch_change(cl)
        descCL = change['Description']
        if re.search("EC_COMMIT", descCL) or re.search("SW_COMMIT", descCL):
            refinedList.append(cl)
    return set(refinedList)

def main():
    parser = argparse.ArgumentParser(description='Script to refine new CLs')
    parser.add_argument('--clSet', type=str, help='shelves in Project/Samsung APL', required=True)
    args = parser.parse_args()
    config = get_config()
    clList = args.clSet

    try:
        with P4Session(config) as p4:
            refinedList = get_clUserList(p4, clList)
    except P4Exception as e:
        print(e)

    print "\n".join(refinedList)


if  __name__ == '__main__':
    main()
