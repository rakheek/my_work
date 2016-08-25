#!/usr/bin/env python

import os
import sys
import argparse
from ConfigParser import SafeConfigParser
from P4Session import P4Session, P4Exception, push_attr

def get_config():
    config = SafeConfigParser()
    if (sys.platform == "win32"):
        configPath = os.path.join('e:', '/', 'EC', 'cad_scripts')
        #osType = 'win'
    elif (sys.platform == "linux2"):
        configPath = os.path.join('/', 'mntdir', 'common', 'ec_scripts')
        #osType = 'linux'
    testIni = os.path.join(configPath, 'tests.ini')
    configIni = os.path.join(configPath, 'config.ini')
    listConfigs = [configIni, testIni]
    config.read(listConfigs)
    return config



def isClMapped(p4, cl, client_name):
    if (cl):
        with push_attr(p4, client=client_name):
            cl_string = "%s%s" % ("//...@=", cl)
            output = p4.run("fstat", "-F", "isMapped", cl_string)

        if(output):
            return 1

    return 0

def main():
    parser = argparse.ArgumentParser(description='script to check cl maps to a client ')
    parser.add_argument('--cl', type=str, help='cl list', required=True)
    parser.add_argument('--cname', type=str, help='client name ', required=True)
    args = parser.parse_args()
    cl = args.cl
    client_name = args.cname

    config = get_config()

    try:
        with P4Session(config) as p4:
            clMapped = isClMapped(p4, cl, client_name)
    except P4Exception as e:
        for e in p4.errors:
            sys.exit(e)

    print clMapped

if  __name__ == '__main__':
    main()

