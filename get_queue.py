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
parser.add_argument('--queue_type', type=str, help='hw/sw', required=True)
args = parser.parse_args()

def get_cl_list(cl_list):
    module_list = ["apitrace", "driver", "compiler", "fs", "cachesim", "ts", "rtl"]
    hw_cl = []
    sw_cl = []
    hw_build_modules = []
    sw_build_modules = []
    for module in module_list:
        for cl in cl_list:
            try:
                client = "%s-%s" % ("quickbuild_sgpu_main", module)
                os.environ["P4CLIENT"] = client
#                p4.set_env("P4CLIENT", "quick_sgpu_main-driver")
                cl_string = "%s%s" % ("//...@=", cl)
#                cmd = ["-T", "isMapped", "cl_string"]
                cmd = "%s %s %s %s %s %s %s" % ("p4", "-c", client, "fstat", "-T", "isMapped", cl_string)
#                output = p4.run_fstat(cmd)
#                isMapped = os.system(cmd)
                proc = subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
                output,err = proc.communicate()
                if(re.search(r'isMapped', output)):
                    if( module == "rtl"):
                        hw_cl.append(cl)
                        hw_build_modules.append(module)
                    else:
                        sw_cl.append(cl)
                        sw_build_modules.append(module)
            except P4Exception:
                for e in p4.errors:
                    print e 
    p4.disconnect()
    return hw_cl, sw_cl, set(hw_build_modules), set(sw_build_modules)

def get_build_type():
    cl_list = args.CL_LIST
    cl_array = cl_list[0].split(" ")
    hw_cl, sw_cl, hw_mods, sw_mods = get_cl_list(cl_array)
    if(args.queue_type == "hw"):
        print " ".join(str(list) for list in hw_mods)
        print " ".join(str(list) for list in hw_cl)
    elif(args.queue_type == "sw"):
        print " ".join(str(list) for list in sw_mods)
        print " ".join(str(list) for list in sw_cl)
    else:
        print "Invalid arguement"
if  __name__ == '__main__':
    get_build_type()
