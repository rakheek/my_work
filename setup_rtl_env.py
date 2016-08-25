#!/mntdir/apps/python_org/2.7.6/bin/python

import os
import re
import sys
import argparse
import glob
import platform
import subprocess
from subprocess import Popen, PIPE
import ConfigParser
from ConfigParser import SafeConfigParser
from common import *
#from common import setLLP, run_drv_trex, cleanup, check_num_images, diff_images, sourceFile, run_rtl_make, run_rtl_test, runCmd

#config = ConfigParser.ConfigParser()
config = SafeConfigParser()
listConfigs = ['/mntdir/common/ec_scripts/config.ini', '/mntdir/common/ec_scripts/tests.ini']
config.read(listConfigs)

parser = argparse.ArgumentParser(description = 'script to setup RTL environment')
parser.add_argument('--setEnv', action='store_true', default=False, help='setup Environment')
args = parser.parse_args()

def getTestDir():
    curDir = os.getcwd()
#    hwDir = config.get('vcs', 'hw_dir')
#    tbDir = config.get('RTL_Builds', tbName)
    aplDir = os.path.join(curDir, 'apl')
#    if not os.path.exists(aplDir):
#        sys.exit("The apl directory soes not exist")
#    testPath = os.path.join(curDir, hwDir, tbDir)
#    if not os.path.exists(testPath):
#        print testPath
#        sys.exit("The test bench does not exist")
#    else:
#        os.chdir(testPath) 
    return curDir, aplDir

def setEnv(aplDir):
#    print aplDir
    escherBashrc = config.get('hw', 'bashrc_file')
    print "Sourcing %s" % escherBashrc
    sourceFile(aplDir, escherBashrc)    
    hwSetup = config.get('hw', 'hw_setup')
    absHwSetup = os.path.join(aplDir, hwSetup)
    print "Sourcing %s" % absHwSetup
    sourceFile(aplDir, absHwSetup)    
#    os.environ['PROJ'] = config.get('hw', 'project')
#    print "The PROJ is set to %s" % os.environ.get('PROJ')
#    os.environ['VCS_LIC_EXPIRE_WARNING'] = config.get('vcs', 'vcs_lic_value')
#    print "VCS_LIC_EXPIRE_WARNING is set to %s" % os.environ['VCS_LIC_EXPIRE_WARNING']
#    os.environ['VCS_ARCH_OVERRIDE'] = config.get('vcs', 'vcs_arch')
#    print "VCS_ARCH_OVERRIDE is set to %s" % os.environ['VCS_ARCH_OVERRIDE']
#    boostPath = os.path.join(aplDir, config.get('vcs', 'boost'))
#    os.environ['BOOST'] = boostPath
#    print "BOOST is set to %s" % os.environ['BOOST']
#    LLP = os.environ.get('LD_LIBRARY_PATH')
#    print LLP
#    boostLib = os.path.join(boostPath, 'lib')
#    hwLLP = "%s:%s" % (boostLib, LLP)
#    print "LD_LIBRARY_PATH is %s" % hwLLP
#    os.environ['LD_LIBRARY_PATH'] = hwLLP

if  __name__ == '__main__':
    arch = 'x64'
    buildType = 'debug'
    curDir, aplDir = getTestDir() 
#    print testPath
    setEnv(aplDir)
    print os.getcwd()
