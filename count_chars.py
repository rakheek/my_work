#!/usr/bin/python

import os
import sys

fp = open("example", "r")
lines = fp.readlines()
for line in lines:
    print len(line)
	
