#!/usr/bin/env python

from xml.etree import ElementTree
import xml.etree.ElementTree as et
import argparse
 
def pinDownXmlParser(inputFile):
    #fRd = open('openbugs.xml', 'r')
    fRd = open(inputFile, 'r')
    try:
        tree = ElementTree.parse(fRd)
        #root = tree.getroot()
        #print root.tag
        #print root.attrib
        #print root
        #print tree

        myDict = {}
        bugNo = ''
        clNo = ''
        line = ''
        committer = ''
        for node in tree.iter('Bug'):
            #print node.tag, node.attrib
            bugNo = node.attrib.get('bugNumber')
            myDict.setdefault(bugNo, [])
            for element in tree.iter('Errorline'):
                line = element.attrib.get('line')
                #print line
            for element in tree.iter('BugCommitInfo'):
                committer = element.attrib.get('committer')
                print committer
            for element in tree.iter('FailingRev'):
                clNo = element.attrib.get('globalRevision')
                #print clNo

            myDict[bugNo].append([clNo, committer, line])

        print myDict

    finally:
        fRd.close()

def main():

    # Command line arguments stuff
    parser = argparse.ArgumentParser(description='pindown xml parser ')
    #parser.add_argument('--l', type=str, help='XML file path', required=True)
    parser.add_argument('--f', type=str, help='filename', required=True)

    args = parser.parse_args()

    #inputFile = "%s/%s" % (args.l, args.f)
    inputFile = "%s" % (args.f)
    print inputFile

    pinDownXmlParser(inputFile)

if __name__ == '__main__':
    main()
