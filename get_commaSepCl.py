#!/usr/bin/env python

import argparse

if  __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Script to output comma seperated CLs')
    parser.add_argument('--clSet', type=str, help='shelves in Project/Samsung APL', required=True)
    args = parser.parse_args()
    clList = args.clSet.split(" ")
    print ",".join(clList)

