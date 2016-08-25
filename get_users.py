#!/mntdir/apps/python_org/2.7.6/bin/python

import os
import re
import sys
import argparse
from P4 import P4, P4Exception
from pprint import pprint
import subprocess
from subprocess import Popen, PIPE


p4=P4()
p4.port = 'aplp4:2001'
p4.user = 'perforce'
p4.password = 'F4658E0CA9D9111798B165E4F1793ADF'
p4.connect()

parser = argparse.ArgumentParser(description = 'script to determine builds from CL')
parser.add_argument('--CL_LIST', nargs='+', type=str, help='CL list', required=True)
parser.add_argument('--user', action='store_true', default=False, help='Get users')
args = parser.parse_args()

def get_user(cl):
    records = p4.run_describe(cl)
#    print records
    for record in records:
        user = record['user']
        client = record['client']
    return user, client
    p4.disconnect()

def submit_cls():
    users = []
    cl_list = args.CL_LIST
    user_flag = args.user
    cl_array = cl_list[0].split(" ")
    for cl in cl_array:
        user, client = get_user(cl)
        users.append(user)
    print " ".join(str(user) for user in users)
if  __name__ == '__main__':
    submit_cls()
