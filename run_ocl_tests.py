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

#config = ConfigParser.ConfigParser()
config = SafeConfigParser()
if (sys.platform == "win32"):
    configPath = os.path.join('e:', '/', 'EC', 'cad_scripts')
    osType = 'win'
elif (sys.platform == "linux2"):
    configPath = os.path.join('/', 'mntdir', 'common', 'ec_scripts')
    osType = 'linux'
testIni = os.path.join(configPath, 'tests.ini')
configIni = os.path.join(configPath, 'config.ini')
print testIni
print configIni
listConfigs = [configIni, testIni]
config.read(listConfigs)

parser = argparse.ArgumentParser(description = 'script to run driver tests for TRex ')
parser.add_argument('--arch', type=str, help='Architecture', required=True, default="x86")
parser.add_argument('--buildType', type=str, help='Build Type', required=True, default="relwithdebinfo")
parser.add_argument('--testName', type=str, help='Test Name', required=True)
args = parser.parse_args()

def getTestDir(testName):
    curDir = os.getcwd()
    configSect = "%s_%s_%s" % ('OCL', osType, 'smoke')
    testDir = os.path.join(curDir, configSect)
    if not os.path.exists(testDir):
        os.mkdir(testDir)
#    regressDir = config.get('GFXBench_linux_smoke', test_dir)
    testPath = os.path.join(curDir, configSect, testName)
    if not os.path.exists(testPath):
        os.mkdir(testPath)
#    shadersDir = os.path.join(testPath, "shadersDir", "")
#    shadersDir = os.path.join(testPath, "shadersDir")
#    print shadersDir
#    if not os.path.exists(shadersDir):
#        os.mkdir(shadersDir)
    return curDir, testPath

    
if  __name__ == '__main__':
    arch = args.arch
    buildType = args.buildType
    testName = args.testName
    configSect = "%s_%s_%s" % ('OCL', osType, 'smoke')
    artifactPath = setLLP(arch, buildType)
    curDir, testPath = getTestDir(testName) 
    print testPath
    print "Cleaning up test directory %s" % testPath
    cleanup(testPath)
    testPath = run_ocl_tests(testName, arch, buildType, testPath, configSect)
