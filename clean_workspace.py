#!/mntdir/apps/python_org/2.7.6/bin/python

import os
import re
import sys
import argparse
from P4 import P4, P4Exception
from pprint import pprint
import ConfigParser
import subprocess
from subprocess import Popen, PIPE

#config = ConfigParser.ConfigParser()
#config.read('config.ini')

parser = argparse.ArgumentParser(description = 'script to clean user WS post EC_PASSED')
parser.add_argument('--cl', type=str, help='shelved cl cleanup', required=True)
parser.add_argument('--force', action='store_true', help='sync latest files', default=False)
args = parser.parse_args()

p4=P4()

def get_user_info():
    try:
        p4.connect()
        p4_info = p4.run("info")[0]
    except P4Exception:
        for e in p4.errors:
            sys.exit(e)

def clean_workspace():
    cl = args.cl
    force = args.force
    try:   
#        p4.run_login()
#        deleteShelve = p4.run_shelve("-c", "-d", cl)
        change = p4.fetch_change(cl)
        desc = change['Description']
        if re.search("EC_PASSED", desc):
            p4.client = change['Client']
            files_inCL = p4.run_opened("-c", cl)
#            depotFiles = change['Files']
            print "deleting shelve %s" % cl
            deleteShelve = p4.run_shelve("-d", "-c", cl)
            for record in files_inCL:
                if(force):
                    print "Force option enabled reverting and syncing %s" % record['clientFile']
                    p4_revert = p4.run_revert("-w", record['clientFile'])
                    p4.run_sync("-f", record['clientFile'])
                else:
                    if (record['action'] == 'add'):
                        print "reverting file %s" % record['clientFile']
                        p4_revert = p4.run_revert("-w", record['clientFile'])
#                        p4.run_sync("-f", record['clientFile'])
                    else:
                        p4_diff = p4.run("diff", "-sa", record['depotFile'])
                        if(p4_diff):
                            sys.exit("You have files opened and are updated %s. Please make a backup for the file and rerun script" % (record['clientFile']))
                        else:
                            print "reverting file %s" % record['clientFile']
                            p4_revert = p4.run_revert(record['clientFile'])
                            p4.run_sync("-f", record['clientFile'])
            print "Deleting CL %s" % cl
            p4.run_change("-d", cl)
        else:
            print "Your CL %s does not have description EC_PASSED. Skipping the CL delete"
    except P4Exception:
        for e in p4.errors:
            sys.exit(e)

    p4.disconnect()

if  __name__ == '__main__':
    get_user_info()
    clean_workspace()
