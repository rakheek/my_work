#!/usr/bin/env python

import os
import sys
import argparse
import subprocess
from subprocess import Popen, PIPE
from ConfigParser import SafeConfigParser

#from P4Session import P4Session, P4Exception

# Example
#ectool --debug 1 publishArtifactVersion --artifactName 'APL:ets-linux.relwithdebinfo' \
#       --compress 1 \
#       --followSymlinks 1 \
#       --repositoryName 'default' \
#       --fromDirectory '/ec_test/work/hw-sw-ci/ec_prod_main-build-ets_hardik.patel/sgpu/main' \
#       --includePatterns 'sw/ets/**/ets-main;_out/linux-x86/**/clog*;_out/linux-x86/**/clog.*' \
#       --version '1.0-hardik.patel_1147'

def publish_artifact(ectoolPath, artfLocation, artfGroup, artfName, artfPatterns, artfVersion):
   
    print("Publish artifact is selected")
        
    artfPublishCmd = "%s %s %s \'%s:%s\' %s %s %s \'%s\' %s \'%s\' %s \'%s\' %s %s " % (ectoolPath, "publishArtifactVersion", "--artifactName", artfGroup, artfName, "--compress 1",  "--followSymlinks 1", "--repositoryName", "default", "--fromDirectory", artfLocation, "--includePatterns", artfPatterns, "--version", artfVersion)
    
    print artfPublishCmd
    
    # Get current working dir
    cwd = os.getcwd()
    print cwd

    # Change dir to artifact dir provided at artfLocation
    os.chdir(artfLocation)

    try:
        result = proc = subprocess.Popen(artfPublishCmd, shell=True, stdout= PIPE)
        for line in iter(result.stdout.readline, ''):
            #print line
            print line.rstrip('\n')
    except OSError as e:
        print ("[OSError] %s" % e.errno)
        print ("[OSError] %s" % e.strerror)
        print ("[OSError] %s" % e.filename)
    except:
        print ("[Error] %s" % sys.exc_info()[0])

    # Retrun back to original working dir
    os.chdir(cwd)
    cwd = os.getcwd()
    print cwd

# Example of retrive Command
#ectool --debug 1 retrieveArtifactVersions --artifactVersionName 'APL:apitrace-windows.relwithdebinfo:1.0-hardik.patel_1145' \
#       --overwrite "update" \
#       --repositoryNames "default" \
#       --toDirectory 'C:/EC/builds/ec_prod_main-build-smoke-windows_hardik.patel/sgpu/main'

def retrive_artifact(ectoolPath, artfLocation, artfGroup, artfName, artfVersion):
    
    print("Retrive artifact is selected")

    artfRetriveCmd = "%s %s %s \'%s:%s:%s\' %s %s %s %s %s %s" % (ectoolPath, "retrieveArtifactVersions", "--artifactVersionName", artfGroup, artfName, artfVersion, "--overwrite", "\"update\"", "--repositoryNames", "\"default\"", "--toDirectory", artfLocation)

    print artfRetriveCmd

    # Get current working dir
    cwd = os.getcwd()
    print cwd

    # Change dir to artifact dir provided at artfLocation
    os.chdir(artfLocation)

    try:
        result = proc = subprocess.Popen(artfRetriveCmd, shell=True, stdout= PIPE)
        for line in iter(result.stdout.readline, ''):
            #print line
            print line.rstrip('\n')
    except OSError as e:
        print ("[OSError] %s" % e.errno)
        print ("[OSError] %s" % e.strerror)
        print ("[OSError] %s" % e.filename)
    except:
        print ("[Error] %s" % sys.exc_info()[0])

    # Retrun back to original working dir
    os.chdir(cwd)
    cwd = os.getcwd()
    print cwd


def main():

    # Command line arguments stuff
    parser = argparse.ArgumentParser(description='script to publish/retrive artifacts')

    parser.add_argument('--a', type=str, help='Artifact name', required=True)
    parser.add_argument('--l', type=str, help='Artifact location', required=True)
    parser.add_argument('--p', type=str, help='Publish artifact', required=True)
    parser.add_argument('--r', type=str, help='Retrive artifact', required=True)
    parser.add_argument('--g', type=str, help='Artifact group name', required=True)
    parser.add_argument('--ip', type=str, help='Artifacts patterns', required=True)
    parser.add_argument('--v', type=str, help='Artifact version', required=True)

    args = parser.parse_args()

    # Ectool command path
    ectool_path = "/opt/electriccloud/electriccommander/bin/ectool"
    
    if (( args.p == 'true') & ( args.r == "false")):
        publish_artifact(ectool_path, args.l, args.g, args.a, args.ip, args.v)
    elif (( args.p == "false") & ( args.r == "true")):
        retrive_artifact(ectool_path, args.l, args.g, args.a, args.v)
    else:
        print("What do you want to do? provide (p)ublish or (r)etrive option at commandline")

if  __name__ == '__main__':
    main()
