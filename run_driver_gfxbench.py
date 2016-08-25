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

#config = ConfigParser.ConfigParser()
config = SafeConfigParser()
listConfigs = ['config.ini', 'tests.ini']
config.read(listConfigs)

parser = argparse.ArgumentParser(description = 'script to run driver tests for GFXBench')
parser.add_argument('--module', type=str, help='Module', required=True, default="compiler")
parser.add_argument('--arch', type=str, help='Architecture', required=True, default="x86")
parser.add_argument('--buildType', type=str, help='Build Type', required=True, default="relwithdebinfo")
parser.add_argument('--testName', type=str, help='Test Name', required=True)
args = parser.parse_args()

def setLLP():
    curDir = os.getcwd()
    aplDir = os.path.join(curDir, "apl")
    sgpuDir = os.path.join(curDir, "sgpu")
    testDir = os.path.join(curDir, "testDir")
    if not os.path.exists(aplDir):
        print "apl and sgpu directories do not exist"
        sys.exit("apl and sgpu directories do not exist")
    platformArch = args.arch
    buildType = args.buildType
    module = args.module
    if(platform.system() == 'Linux'):
        osPlatform = 'Linux'
    artifactArch = "%s-%s" % (osPlatform.lower(), platformArch)        
    externLibsPath = os.path.join("extern", "libs")
    print externLibsPath
    externToolsPath = os.path.join("extern", "tools")
    print externToolsPath
    modStr = "%s-%s" % ("main", module)
    pocoLibPath = os.path.join(aplDir, externLibsPath, "poco-1.4.6", "bin", osPlatform, "32bit")
    libYamlPath = os.path.join(aplDir, externLibsPath, "libyaml-0.1.6", "bin", osPlatform, "64bit") 
    imageMagickLibPath = os.path.join(aplDir, externToolsPath, osPlatform.lower(), "x64", "imagemagick", "6.8.7-10", "lib") 
    imageMagickBinPath = os.path.join(aplDir, externToolsPath, osPlatform.lower(), "x64", "imagemagick", "6.8.7-10", "bin") 
    gcc64Path = os.path.join(aplDir, externToolsPath, osPlatform.lower(), "x64", "gcc", "4.8.2", "lib64") 
    gccPath = os.path.join(aplDir, externToolsPath, osPlatform.lower(), "x64", "gcc", "4.8.2", "lib") 
    artifactPath = os.path.join(sgpuDir, "main", "_out", artifactArch, buildType)
#    LPP = "%s:%s:%s:%s:%s" % (artifactPath, pocoLibPath, libYamlPath, imageMagickPath)
    LLP = "%s:%s:%s:%s:%s:%s" % (artifactPath, pocoLibPath, libYamlPath, imageMagickLibPath, gccPath, gcc64Path)
    print LLP
    os.environ["LD_LIBRARY_PATH"] = LLP
    path = os.environ.get('PATH')
    os.environ['PATH'] = "%s:%s" % (imageMagickBinPath, path)
    if not os.path.exists(testDir):
        os.mkdir(testDir)
    return curDir, aplDir, testDir

def matchTestDir(testDir):
    testName = args.testName
    print testName
    testConfig = config.get('GFXBench_tests', testName)
    print testConfig
    testConfigDir = os.path.join(testDir, testConfig)
    shadersDir = os.path.join(testConfigDir, "shadersDir", "")
    if not os.path.exists(testConfigDir):
        os.mkdir(testConfigDir)
    print testConfigDir
    return testConfigDir, shadersDir

    
def run_drv_gfxbench(curDir, aplDir, testRunDir, shadersDir):
    testName = args.testName
    imageBin = config.get('GFXBench_linux_smoke', 'image_bin') 
    buildType = args.buildType
    buildEsemuPath = os.path.join(aplDir, "tests", "apps", "GFXBench", "3.0", "build_es_emu")
    imageAbsBin = os.path.join(buildEsemuPath, buildType, imageBin)
    print imageBin
    os.environ['SGPU_APP_FRAME_NUM'] = '0'
    os.environ['SGPU_DUMP_SHADERS_TO'] = shadersDir
    if not os.path.exists(shadersDir):
        os.mkdir(shadersDir)
    os.chdir(testRunDir)
    cmd = "%s %s %s %s %s" % (imageAbsBin, "-b", buildEsemuPath, "-t", testName) 
    print cmd
    try:
        proc = subprocess.Popen(cmd, shell=True, stdout=PIPE)
        for line in iter(proc.stdout.readline, b''):
            print line,
#        proc = subprocess.call(cmd, shell=True)
        output,err = proc.communicate()
    except:
        e = sys.exc_info()[1]
        print "Error: %s" % e
    return buildEsemuPath

def cleanup(testRunDir):
    if os.path.exists(testRunDir):
        for file in os.listdir(testRunDir):
#        if re.search("png", file):
            try: 
                os.remove(os.path.join(testRunDir, file))   
            except OSError as e:
                print e               
    
def check_num_images(testRunDir):
    expNumImages = config.get('GFXBench_tests', 'num_images')
    fileList = glob.glob("*.png")
    genNumImages = len(fileList)
    if (genNumImages != int(expNumImages)):
        message = "The number of images is %s and not %s as expected" % (genNumImages, expNumImages)
        sys.exit(message)
    else:
        print "Number of images generated is %s as expected" % (genNumImages)
    
def compare_images(testConfigDir, build_es_emu):
    goldDir = config.get('GFXBench_linux_smoke', 'gold_dir')
    testName = os.path.basename(testConfigDir)
    basePath = os.path.join(build_es_emu, "regress")
    imgFiles = []
    for file in  os.listdir(testConfigDir):
        if file.endswith(".png"):
            imgFiles.append(file)
            count = 0
            goldImage = os.path.join(basePath, testName, goldDir, file)
            print goldImage
            genImage = os.path.join(testConfigDir, file)
            print genImage
            diff = "diff-" + file 
            cmpCmd = ["compare", "-metric", "ae", genImage, goldImage, diff]
            print cmpCmd
            ret = subprocess.Popen(cmpCmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (out,err)= ret.communicate()
            count += 1
            print err
            if (int(err) > 0):
                print "Test Failed  for %s : FAIL" % (file)
                print "Please check diff file: %s" % (diff)
            else:
                print "Test Passed for %s: PASS" % (file)
                                                                                                            
if  __name__ == '__main__':
    curDir, aplDir, testDir = setLLP()
    testConfigDir, shadersDir = matchTestDir(testDir)
    cleanup(shadersDir)
    cleanup(testConfigDir)
    build_es_emu = run_drv_gfxbench(curDir, aplDir, testConfigDir, shadersDir)
    check_num_images(testConfigDir)
    compare_images(testConfigDir, build_es_emu)

