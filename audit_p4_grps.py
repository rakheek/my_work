#!/home/apps/python_org/2.7.6/bin/python

import os
import sys
from P4 import P4

p4=P4()

def audit_p4_grps():
    p4.port = 'aplp4:2001'
    p4.user = 'rakhee.k'
    try:
        p4.connect()
        groups = p4.run('groups')
        for group in groups:
            print "%s, %s" % (group['group'], group['user'])
    except P4Exception:
        for e in p4.errors:
            print e 
	
if  __name__ == '__main__':
    audit_p4_grps()
