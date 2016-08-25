#!/usr/bin/python

import os
import sys
from pprint import pprint

modules_mntdir=[]
modules_home=[]
fp = open("py_modules_mntdir", "r")
lines = fp.readlines()
for line in lines:
    mod_in_line = line.split(" ")
    for mod in mod_in_line:
        if(mod !=''):
            modules_mntdir.append(mod.rstrip())
fp = open("py_modules_home", "r")
lines = fp.readlines()
for line in lines:
    mod_in_line = line.split(" ")
    for mod in mod_in_line:
        if(mod !=''):
            modules_home.append(mod.rstrip())
diff_mod = list(set(modules_home) - set(modules_mntdir)) 
print "List of modules in Home and not in mntdir\n"
pprint(diff_mod)
print "List of modules in mntdir and not in home\n"
pprint(set(modules_mntdir) - set(modules_home))
