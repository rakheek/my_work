#!/usr/bin/env python

import os
import sys
import argparse
from ConfigParser import SafeConfigParser
from P4Session import P4Session, P4Exception


def get_config():
    config = SafeConfigParser()
    if (sys.platform == "win32"):
        configPath = os.path.join('e:', '/', 'EC', 'cad_scripts')
        osType = 'win'
    elif (sys.platform == "linux2"):
        configPath = os.path.join('/', 'mntdir', 'common', 'ec_scripts_test')
        osType = 'linux'
    testIni = os.path.join(configPath, 'tests.ini')
    configIni = os.path.join(configPath, 'config.ini')
    listConfigs = [configIni, testIni]
    config.read(listConfigs)
    return config


def get_clModList(p4):
    if(args.cl):
        clList = args.cl
    if(args.build_type):
        buildType = args.build_type
    queue = args.queue_type
    branch = args.branch_name
    moduleList = config.get(queue, 'modules')
    if(buildType == 'daily' or buildType == 'psci'):
        build_modules = moduleList.split(" ")
    else:
        prefix = config.get(queue, 'clientPrefix')
        clientPrefix = "%s_%s" % (prefix, branch)
#        clList = clList.replace("\\n", "\n")
        clList = clList.split(',')
        modules = moduleList.split(" ")
        modList = []
        for mod in modules:
            modList.append(mod)
        build_modules = []
        for module in modList:
            for cl in clList:
                try:
                    client = "%s-%s" % (clientPrefix, module)
                    p4.client = client
                    cl_string = "%s%s" % ("//...@=", cl)
                    output = p4.run("fstat", "-F", "isMapped", cl_string)
                    if(output):
                        build_modules.append(module)
                        if module == "compiler":
                            build_modules.append("driver")
                        if module == "driver":
                            build_modules.append("ocl")
                except P4Exception:
                    for e in p4.errors:
                        sys.exit(e)
        depend_mods = ['compiler', 'driver', 'fs', 'ocl']
        build_mods = set(build_modules)
        if set(build_mods).intersection(depend_mods):
            build_modules.append('ets')
    return set(build_modules)

def main():
    global args, config

    parser = argparse.ArgumentParser(description='script to get shelved CLs matching description by queue')
    parser.add_argument('--queue_type', type=str, help='hw/sw', required=True)
    parser.add_argument('--branch_name', type=str, help='branch name', required=True)
    parser.add_argument('--cl', type=str, help='cl list', required=False)
    parser.add_argument('--build_type', type=str, help='build type', required=False, default='ci')
    args = parser.parse_args()
    config = get_config()

    try:
        with P4Session(config) as p4:
            build_modules = get_clModList(p4)

    except P4Exception as e:
        print(e)

    for mod in build_modules:
        print mod

if  __name__ == '__main__':
    main()

