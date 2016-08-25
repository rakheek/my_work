#!/mntdir/apps/python_org/2.7.6/bin/python

import os
import re
import sys
import argparse
from P4 import P4, P4Exception
from pprint import pprint

p4=P4()
p4.port = 'aplp4:2001'
p4.user = 'perforce'
p4.password = 'F4658E0CA9D9111798B165E4F1793ADF'

parser = argparse.ArgumentParser(description = 'script to find file differences in streams')
parser.add_argument('--parent_stream', type=str, help='parent stream name as in main-impl-integ-dev', required=True)
parser.add_argument('--child_stream', type=str, help='child stream name as in main-impl-peq-dev', required=True)
args = parser.parse_args()

def get_p4_files(stream_pattern):
    p4_files_list = []
    depot_files = "%s%s" % (stream_pattern, "...")
    try:
        p4.connect()
        files = p4.run('files', depot_files)
        for file in files:
            p4File = file['depotFile']
            file = re.sub(stream_pattern, '', p4File.rstrip())
            p4_files_list.append(file)
    except P4Exception:
        for e in p4.errors:
            print e 
    p4.disconnect()
    return p4_files_list

def audit_p4_stream_data():
    parent = args.parent_stream
    child = args.child_stream
    parent_pattern = "%s%s%s" % ('//sgpu/', parent, '/')
    child_pattern = "%s%s%s" % ('//sgpu/', child, '/')
    parent_files_list = get_p4_files(parent_pattern)
    child_files_list = get_p4_files(child_pattern)
    diff_list = set(child_files_list) - set(parent_files_list)
    print "Here is the list of files in %s and not in %s\n" % (child, parent)
    print "Please check for case differences"
    for item in diff_list:
        print "%s%s" % (child_pattern, item)
#    pprint(diff_list)

if  __name__ == '__main__':
    audit_p4_stream_data()
