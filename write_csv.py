#!/usr/bin/python

import os
import sys

inputfile = sys.argv[1]
outfile = sys.argv[2]

def getSize(filename):
    st = os.stat(filename)
    return st.st_size

def write_csv():
    fout = open(outfile, "w")
    fin = open(inputfile, "r")
    lines = fin.readlines() 
    for line in lines:
        print line
        filesize, filename = line.split(" \/")
        filesize_in_G = int(filesize)/(1024 *1024)
        fout.write("%s%s %s %s\n" % (filesize_in_G,"G","," ,filename))
	
if  __name__ == '__main__':
    write_csv()
