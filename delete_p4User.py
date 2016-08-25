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


config = ConfigParser.ConfigParser()
config.read('config.ini')

parser = argparse.ArgumentParser(description = 'Script to delete user')
parser.add_argument('--user', type=str, help='user that needs delete', required=True)
args = parser.parse_args()

p4=P4()

p4.port = config.get('p4_server', 'P4PORT')
p4.user = config.get('p4_server', 'P4USER')
p4.password = config.get('p4_server', 'P4TICKET')
#p4.password = config.get('p4_server', 'P4TICKET')

p4.connect()

def del_userShelves():
    user = args.user
    try:   
        p4.run_login()
        userShelves = p4.run_changes("-s", "shelved", "-u", user)
        for key in userShelves:
            print "Deleting shelves for user %s %s" % (user, key['change'])
            p4.run_shelve("-f", "-d", "-c", key['change'])
        userPending = p4.run_changes("-s", "pending", "-u", user)
        for key1 in userPending:
            print "Deleting pending changes for user %s" % key1['change']
            p4.run_change("-f", "-d", key1['change'])
        userClients = p4.run_clients("-u", user)
        for ws in userClients:
            print "Deleting client %s for user %s" % (ws['client'], user)
            p4.run_client("-f", "-d", ws['client'])
        userGroups = p4.run_groups("-u", user)
        for groupName in userGroups:
            print "Please remove user %s from group %s" % (user, groupName['group'])
        p4.run_user("-d", "-f", user)
    except P4Exception:
        for e in p4.errors:
            sys.exit(e)

    p4.disconnect()

if  __name__ == '__main__':
    user = args.user
    del_userShelves()
