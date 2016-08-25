#!/usr/bin/env python

import argparse
import ConfigParser

from P4Session import P4Session, P4Exception

def get_lastGoodCL(p4, branch):
    branchString = "//%s/%s/%s" % ("sgpu", branch, "...")
    lastChange = p4.run_changes("-s", "submitted", "-m1", branchString)
    return lastChange

def get_config():
    config = ConfigParser.ConfigParser()
    config.read('config.ini')
    return config

def main():
    parser = argparse.ArgumentParser(description='script to get TOT')
    parser.add_argument('--branch_name', type=str, help='branch_name', required=False, default='main')
    parser.add_argument('--site_name', type=str, help='site', required=False)
    args = parser.parse_args()
    config = get_config()

    try:
        with P4Session(config) as p4:
            lastChange = get_lastGoodCL(p4, args.branch_name)

            for key in lastChange:
                print(key['change'])

    except P4Exception as e:
        print(e)


if  __name__ == '__main__':
    main()
