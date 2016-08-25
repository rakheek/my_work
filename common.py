
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
if (sys.platform == "win32"):
    configPath = os.path.join('e:', '/', 'EC', 'cad_scripts')
elif (sys.platform == "linux2"):
    configPath = os.path.join('/', 'mntdir', 'common', 'ec_scripts')
testIni = os.path.join(configPath, 'tests.ini')
configIni = os.path.join(configPath, 'config.ini')
print testIni
print configIni
listConfigs = [configIni, testIni]
config.read(listConfigs)

def setAplSgpu():
    curDir = os.getcwd()
    aplDir = os.path.join(curDir, "apl")
    sgpuDir = os.path.join(curDir, "sgpu")
    return curDir, aplDir, sgpuDir

def setLLP(arch, buildType):
    curDir, aplDir, sgpuDir = setAplSgpu()
    print "Running setLLP in %s" % curDir
    print "APL Dir is %s" % aplDir
    print "SGPU Dir is %s" % sgpuDir
    if not os.path.exists(aplDir):
        print "apl and sgpu directories do not exist"
        sys.exit("apl and sgpu directories do not exist")
    pocoVer = config.get("common", "poco_version")
    yamlVer = config.get("common", "yaml_version")
    gccVer = config.get("common", "gcc_version")
    if(platform.system() == 'Linux'):
        imgMagVer = config.get("common", "imageMagick_linux_version")
    elif(platform.system() == 'Windows'):
        imgMagVer = config.get("common", "imageMagick_win_version")
    glibPath = config.get("common", "glib_path")
    branch = config.get("common", "branch")
    if(platform.system() == 'Linux'):
        osPlatform = 'Linux'
    elif(platform.system() == 'Windows'):
        osPlatform = 'Windows'
    externLibsPath = os.path.join("extern", "libs")
    print externLibsPath
    externToolsPath = os.path.join("extern", "tools")
    print externToolsPath
    artifactArch = "%s-%s" % (osPlatform.lower(), arch)        
    artifactPath = os.path.join(sgpuDir, 'main', "_out", artifactArch, buildType)
    pocoLibPath = os.path.join(aplDir, externLibsPath, pocoVer, "bin", osPlatform, "32bit")
    libYamlPath = os.path.join(aplDir, externLibsPath, yamlVer, "bin", osPlatform, "64bit") 
    imageMagickLibPath = os.path.join(aplDir, externToolsPath, osPlatform.lower(), "x64", "imagemagick", imgMagVer, "lib") 
    if (sys.platform == "win32"):
        imageMagickBinPath = os.path.join(aplDir, externToolsPath, osPlatform.lower(), "x86", "imagemagick", imgMagVer) 
    elif (sys.platform == "linux2"):
        imageMagickBinPath = os.path.join(aplDir, externToolsPath, osPlatform.lower(), "x64", "imagemagick", imgMagVer, "bin") 
    gcc64Path = os.path.join(aplDir, externToolsPath, osPlatform.lower(), "x64", "gcc", gccVer, "lib64") 
    gcc32Path = os.path.join(aplDir, externToolsPath, osPlatform.lower(), "x64", "gcc", gccVer, "lib") 
    gccPath = os.path.join(aplDir, externToolsPath, osPlatform.lower(), "x64", "gcc", gccVer, "bin") 
#    LPP = "%s:%s:%s:%s:%s" % (artifactPath, pocoLibPath, libYamlPath, imageMagickPath)
    LLP = "%s:%s:%s:%s:%s:%s:%s" % (artifactPath, pocoLibPath, libYamlPath, imageMagickLibPath, gcc64Path, gcc32Path, glibPath)
    os.environ["LD_LIBRARY_PATH"] = LLP
    print "LD_LIBRARY_PATH is %s\n" % LLP
    path = os.environ.get('PATH')
    print "Orig path is %s" % path
    print imageMagickBinPath
    if (sys.platform == "linux2"):
        os.environ["PATH"] = "%s:%s:%s" % (gccPath, imageMagickBinPath, path)
    if (sys.platform == "win32"):
        os.environ["PATH"] = "%s;%s;%s;%s;%s" % (artifactPath, imageMagickBinPath, pocoLibPath, libYamlPath, path)
    print "PATH is %s\n" % os.environ.get("PATH")
    return artifactPath

def sourceFile(aplDir, fileName):
    sourceStr = "%s %s" % ('source', fileName)
    command = ['bash', '-c', sourceStr]
    try:
        proc = subprocess.Popen(command, stdout = subprocess.PIPE)
        out, err = proc.communicate()
    except OSError as e:
        print e

def runCmd(cmd):
    command = ['bash', '-c', cmd]
    try:
        proc = subprocess.Popen(command, stdout = subprocess.PIPE)
        out, err = proc.communicate()
        print out
    except OSError as e:
        print e

def run_rtl_make(tbName, make_cmd):
    ncores = config.get('vcs', 'ncores')
    cmd = "%s %s %s %s" % ('make', '-j', ncores, make_cmd)
    try:
        proc = subprocess.Popen(cmd, shell=True, stdout=PIPE)
        for line in iter(proc.stdout.readline, b''):
            print line,
#        proc = subprocess.call(cmd, shell=True)
        output,err = proc.communicate()
    except:
        e = sys.exc_info()[1]
        print "Error: %s" % e
        sys.exit(e)

def run_rtl_test(tbName, regressCmd, testList):
    testStr = "%s=%s" % ('TESTLIST', testList)   
    if (tbName == 'pe_fpu'):
        args = 'SKNOBS_ARGS="+*random=5"'
        cmd = "%s %s %s %s" % (regressCmd, testStr, args)
    else:
        cmd = "%s %s %s" % (regressCmd, '-tl', testList)
    try:
        print "running %s" % cmd
        proc = subprocess.Popen(cmd, shell=True, stdout=PIPE)
        for line in iter(proc.stdout.readline, b''):
            print line,
#        proc = subprocess.call(cmd, shell=True)
        output,err = proc.communicate()
    except:
        e = sys.exc_info()[1]
        print "Error: %s" % e
        sys.exit(e)
    print output
    if (re.search(output, 'FAIL')):
        print "Test Failed for %s" % testList

def run_ocl_tests(testName, arch, buildType, testPath, configSect):
    curDir, aplDir, sgpuDir = setAplSgpu()
    testDir = config.get(configSect, 'testDir')
    imageBin = config.get(configSect, 'image_bin')
    imageBinPath = os.path.join(curDir, imageBin)
    print imageBinPath
    testArgs = config.get(configSect, 'testArgs')
    if not os.path.exists(imageBinPath):
        err = "%s can not be found in %s" % (imageBin, imageBinPath)
        sys.exit(err)
    try:
        os.chdir(testPath)
    except OSError as e:
        sys.exit(e)
    cmd = "%s %s %s %s %s %s %s %s %s %s %s" % (imageBinPath, "-b", os.path.dirname(imageBinPath), "-c", "0", "-t", testName, "-e", testArgs, "-o", testPath) 
    print "Running %s in %s" % (cmd, os.getcwd())
    try:
        proc = subprocess.Popen(cmd, shell=True, stdout=PIPE)
        for line in iter(proc.stdout.readline, b''):
            print line,
#        proc = subprocess.call(cmd, shell=True)
        output,err = proc.communicate()
    except:
        e = sys.exc_info()[1]
        print "Error: %s" % e
        sys.exit(e)
    return testPath

def run_drv_trex(testName, buildType, testPath, artifactPath, configSect):
    curDir, aplDir, sgpuDir = setAplSgpu()
    testDir = config.get(configSect, 'testDir')
    imageBin = config.get(configSect, 'image_bin')
    imageBinPath = os.path.join(artifactPath, imageBin)
    print imageBinPath
    absTestName = os.path.join(curDir, testName)
    if not os.path.exists(imageBinPath):
        err = "%s can not be found in %s" % (imageBin, imageBinPath)
        sys.exit(err)
    shadersDir = os.path.join(testPath, "shadersDir", "")
    print shadersDir
#    os.environ['SGPU_APP_FRAME_NUM'] = '0'
    os.environ['SGPU_DUMP_SHADERS_TO'] = shadersDir
    try:
        os.chdir(testPath)
    except OSError as e:
        sys.exit(e)
#    cmd = "%s %s %s %s %s" % (imageBinPath, "-b", basePath, "-t", testName) 
    cmd = "%s %s %s" % (imageBinPath, "-t", absTestName) 
    print "Running %s in %s" % (cmd, os.getcwd())
    try:
        proc = subprocess.Popen(cmd, shell=True, stdout=PIPE)
        for line in iter(proc.stdout.readline, b''):
            print line,
#        proc = subprocess.call(cmd, shell=True)
        output,err = proc.communicate()
    except:
        e = sys.exc_info()[1]
        print "Error: %s" % e
        sys.exit(e)
    return testPath

def run_drv_gfxbench(testName, buildType, configSect):
    curDir, aplDir, sgpuDir = setAplSgpu()
    baseDir = config.get(configSect, 'base_dir')
    basePath = os.path.join(curDir, baseDir)
    imageBin = config.get(configSect, 'image_bin')
    testPath = os.path.join(curDir, configSect, testName)
    imageBinPath = os.path.join(curDir, basePath, buildType, imageBin)
    print imageBinPath
    shadersDir = os.path.join(testPath, "shadersDir", "")
#    if (sys.platform == "win32"):
#        imgCmd = "%s %s '%s'" % ('cygpath', '-a', imageBinPath)
#        proc = subprocess.Popen(imgCmd, shell=True, stdout=PIPE)
#        imageBinPath,err = proc.communicate()
#        print imageBinPath
#        baseCmd = "%s %s '%s'" % ('cygpath', '-a', basePath)
#        proc = subprocess.Popen(baseCmd, shell=True, stdout=PIPE)
#        basePath,err = proc.communicate()
#    os.environ['SGPU_APP_FRAME_NUM'] = '0'
    os.environ['SGPU_DUMP_SHADERS_TO'] = shadersDir
    try:
        os.chdir(testPath)
    except OSError as e:
        sys.exit(e)
    cmd = "%s %s %s %s %s" % (imageBinPath, "-b", basePath, "-t", testName) 
#    cmd = "%s %s %s %s %s" % (imageBinPath, "-b", basePath, "-t", "f131_480x270") 
    print "Running %s in %s" % (cmd, os.getcwd())
    try:
        proc = subprocess.Popen(cmd, shell=True, stdout=PIPE)
        for line in iter(proc.stdout.readline, b''):
            print line,
#        proc = subprocess.call(cmd, shell=True)
        output,err = proc.communicate()
    except:
        e = sys.exc_info()[1]
        print "Error: %s" % e
        sys.exit(e)
#    return testPath

def cleanup(testRunDir):
    if os.path.exists(testRunDir):
        for file in os.listdir(testRunDir):
            if re.search("png", file):
                try: 
                    os.remove(os.path.join(testRunDir, file))   
                except OSError as e:
                    print e               
    
def check_num_images(expNumImages):
    fileList = glob.glob("*.png")
    genNumImages = len(fileList)
    if (genNumImages != int(expNumImages)):
        message = "The number of images is %s and not %s as expected" % (genNumImages, expNumImages)
        sys.exit(message)
    else:
        print "Number of images generated is %s as expected" % (genNumImages)
    
def diff_images(testPath, goldPath):
    imgFiles = []
    for file in  os.listdir(testPath):
        if file.endswith(".png"):
            imgFiles.append(file)
            count = 0
            goldImage = os.path.join(goldPath, file)
            print goldImage
            genImage = os.path.join(testPath, file)
            print genImage
            diff = "diff-" + file 
            if (sys.platform == "win32"):
                compareCmd = "compare.exe"
            elif (sys.platform == "linux2"):
                compareCmd = 'compare'
            cmpCmd = [compareCmd, "-metric", "ae", genImage, goldImage, diff]
            print cmpCmd
#            ret = subprocess.call(cmpCmd, shell=True)
            ret = subprocess.Popen(cmpCmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (out,err)= ret.communicate()
            print out
            count += 1
            print err
            if (ret.returncode != 0):
#            if (ret != 0):
                print "Test Failed  for %s : FAIL" % (file)
                print "Please check diff file: %s" % (diff)
            else:
                print "Test Passed for %s: PASS" % (file)
                                                                                                            
#if  __name__ == '__main__':
#    curDir, aplDir, testDir = setLLP()
#    testConfigDir, shadersDir = matchTestDir(testDir)
#    cleanup(shadersDir)
#    cleanup(testConfigDir)
#    build_es_emu = run_drv_gfxbench(curDir, aplDir, testConfigDir, shadersDir)
#    check_num_images(testConfigDir)
#    compare_images(testConfigDir, build_es_emu)

