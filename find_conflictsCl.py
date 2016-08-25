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


def findConflict(files):
    conflictFlag = 'false'
    setFiles = set(files)
    dup = []
    for f in files:
        if f in setFiles:
            setFiles.remove(f)
        else:
            dup.append(f)
    if dup:
        conflictFlag = "true"
    return conflictFlag

def getFiles(p4, clList):
    files = []
    for cl in clList:
        change = p4.run_describe("-S", cl)
        for item in change:
            for f in item['depotFile']:
                files.append(f)
    return files


def main():
    parser = argparse.ArgumentParser(description='script to get find conflicts in shelved CLs')
    parser.add_argument('--cl', type=str, help='cl list', required=True)
    args = parser.parse_args()
    newLine_seperated_cl = args.cl
    clList = newLine_seperated_cl.replace("\\n", "\n")
    clList = clList.split('\n')

    config = get_config()

    try:
        with P4Session(config) as p4:
            files = getFiles(p4, clList)
            conflict = findConflict(files)
    except P4Exception as e:
        for e in p4.errors:
            sys.exit(e)

    print conflict


if  __name__ == '__main__':
    main()
