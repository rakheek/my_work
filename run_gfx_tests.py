
import os
import re
import sys
import argparse
import glob
import platform
import subprocess
import shutil
from subprocess import Popen, PIPE
import ConfigParser
from ConfigParser import SafeConfigParser
from common import setAplSgpu, setLLP, run_drv_gfxbench, cleanup, check_num_images, diff_images

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

parser = argparse.ArgumentParser(description = 'script to run driver tests for GFXBench')
parser.add_argument('--arch', type=str, help='Architecture', required=True, default="x86")
parser.add_argument('--buildType', type=str, help='Build Type', required=True, default="relwithdebinfo")
parser.add_argument('--testName', type=str, help='Test Name', required=True)
args = parser.parse_args()

def getTestDir(testName):
    curDir = os.getcwd()
    configSect = "%s_%s_%s" % ('GFXBench30', osType, 'smoke')
    testDir = configSect
    if not os.path.exists(testDir):
        os.mkdir(testDir)
#    regressDir = config.get('GFXBench30_linux_smoke', test_dir)
    testPath = os.path.join(curDir, configSect, testName)
    if not os.path.exists(testPath):
        os.mkdir(testPath)
#    shadersDir = os.path.join(testPath, "shadersDir", "")
    shadersDir = os.path.join(testPath, "shadersDir")
    print shadersDir
    if not os.path.exists(shadersDir):
        os.mkdir(shadersDir)
    return curDir, testPath, shadersDir

def cp_configs(curDir, testName, testPath):
    configsDir = config.get('GFXBench_smoke_tests', 'configs_path')
    fsConfig = config.get('GFXBench_smoke_tests', 'fs_config')
    configFile = os.path.join(curDir, configsDir, fsConfig)
    fsWorkDir = os.path.join(testPath, 'fs.properties')
#    print "Copying FS properties from %s to %s" % (configFile, fsWorkDir)
#    shutil.copy(configFile, fsWorkDir)
#    if os.path.exists(os.path.join(configsDir, testName, 'fs.properties'):
#        with open(fsWorkDir, 'a') as f:
#            open(os.path.join(configsDir, testName, 'fs.properties'), 'r')

    
if  __name__ == '__main__':
    arch = args.arch
    buildType = args.buildType
    test = args.testName
    configSect = "%s_%s_%s" % ('GFXBench30', osType, 'smoke')
    testName = config.get('GFXBench_smoke_tests', test)
    artifactsPath = setLLP(arch, buildType)
    curDir, testPath, shadersDir = getTestDir(testName) 
    print testPath, shadersDir
    print "Cleaning up test directory %s" % testPath
    cleanup(testPath)
    print "Cleaning up shaders directory %s" % shadersDir
    cleanup(shadersDir)
    cp_configs(curDir, testName, testPath)
    run_drv_gfxbench(testName, buildType, configSect)
    expNumImages = config.get('GFXBench_smoke_tests', 'num_images')
    check_num_images(expNumImages)
    baseDir = config.get(configSect, 'base_dir')
    basePath = os.path.join(curDir, baseDir, "regress")
    print basePath
    goldDir = config.get(configSect, 'gold_dir')
    goldPath = os.path.join(basePath, testName, goldDir)
    diff_images(testPath, goldPath)
