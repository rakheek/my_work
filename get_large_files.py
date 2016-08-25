#!/usr/bin/python

import os
import sys

root_dir = sys.argv[1]

def getSize(filename):
    st = os.stat(filename)
    return st.st_size

def find_file_size():
    with open("large_files.txt", "w") as fout:
        for root, subFolders, files in os.walk(root_dir):
            for file in files: 
                filename = os.path.join(root, file)
                filesize = getSize(filename)
                if(filesize > 524288000):
                    fout.write("%s %s\n" % (filesize,filename))
#            print os.path.getsize(file)
	
if  __name__ == '__main__':
    find_file_size()
