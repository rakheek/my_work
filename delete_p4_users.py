#!/home/apps/python_org/2.7.6/bin/python

import os
import sys
from P4 import P4
from pprint import pprint

p4=P4()

def delete_users(users):
    p4.port = 'aplp4:2001'
    p4.user = 'p4scripts'
    p4.password = 'p4adminuser'
    try:
        p4.connect()
        for user in users:
#        for group in groups:
#            print "%s, %s" % (group['group'], group['user'])
    except P4Exception:
        for e in p4.errors:
            print e 
	
if  __name__ == '__main__':
    users = []
    f = open('list_users_delete', 'r')
    lines = f.readlines()
    for line in lines:
        users.append(line.strip('\n'))
    pprint(users)
    delete_users(users)
