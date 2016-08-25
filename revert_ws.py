
import os
import sys
import argparse
from ConfigParser import SafeConfigParser

from P4Session import P4Session, P4Exception, push_attr

def get_config():
    config = SafeConfigParser()
    if (sys.platform == "win32"):
        configPath = os.path.join('e:', '/', 'EC', 'cad_scripts')
        #osType = 'win'
    elif (sys.platform == "linux2"):
        configPath = os.path.join('/', 'mntdir', 'common', 'ec_scripts_test')
        #osType = 'linux'
    testIni = os.path.join(configPath, 'tests.ini')
    configIni = os.path.join(configPath, 'config.ini')
    print testIni
    print configIni
    listConfigs = [configIni, testIni]
    config.read(listConfigs)
    return config


def revert_ws(p4, client):
    with push_attr(p4, client=client):
        p4.run("client", "-o")
        print "Reverting files from %s" % client
        revertOut = p4.run("revert", "-w", "//...")
        if (revertOut == []):
            print "No files  opened on client\n"
        else:
            print revertOut

def main():
    desc = """ Script to revert WS from the workspace argument or
            workspace created by arguments for modules, agent, branch"""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--module', type=str, help='module name', required=False)
    parser.add_argument('--build_path', type=str, help='build path', required=False)
    parser.add_argument('--client', type=str, help='client name', required=False)
    parser.add_argument('--branch', type=str, help='branch name', required=False)
    parser.add_argument('--site_name', type=str, help='site name', required=False)
    args = parser.parse_args()
    site_name = args.site_name

    if (args.client):
        client = args.client
    elif(args.module and args.build_path):
        module = args.module
        path = args.build_path
        agent = os.path.basename(path)
        client = "%s-%s-%s-%s" % ("ec", args.branch, module, agent)
    else:
        sys.exit("No workspace to refresh")

    config = get_config()

    try:
        with P4Session(config, site_name) as p4:
            revert_ws(p4, client)
    except P4Exception:
        for e in p4.errors:
            print e

if  __name__ == '__main__':
    main()

