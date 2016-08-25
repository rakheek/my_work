#!/usr/bin/python

import os
import sys

infile = sys.argv[1]

def get_p4_revs():
    fin = open(infile, "r")
    p4_files = fin.readlines()
    for file in p4_files:
        cmd = "%s %s %s" % ("p4", "filelog", file)
        try:
            os.system(cmd)
        except IOError, e:
            print e
                     
	
if  __name__ == '__main__':
    get_p4_revs()
