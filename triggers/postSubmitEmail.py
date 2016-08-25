#!/mntdir/apps/python_org/2.7.6/bin/python

#TODO check the code in tonight to fix messages for non EC_COMMIT shelves

import os
import re
import sys
import argparse
from P4 import P4, P4Exception
from pprint import pprint
import ConfigParser
from ConfigParser import SafeConfigParser
import subprocess
from subprocess import Popen, PIPE
import smtplib
from smtplib import SMTPException
from email.mime.text import MIMEText
import logging
from termcolor import colored
from check_smoke import check_smoke_run
from datetime import datetime

config = ConfigParser.ConfigParser()
configIni = 'emailConfig.ini'
config.read(configIni)

p4=P4()

p4.port = 'aplp4:2001'
p4.user = 'p4scripts'
p4.password = 'p4adminuser'

p4.connect()

#parser = argparse.ArgumentParser(description = 'script to Sanity check shelves with EC_COMMIT')
#parser.add_argument('--cl', type=str, help='shelved cl', required=True)
#args = parser.parse_args()

branch = 'main'

if(len(sys.argv) > 3):
    dataDir = os.getcwd()
else:
    dataDir = "%s/%s" % ("/mntdir/common/ec_data", branch)

def sendEmail(file, cl, sect):
    sender = 'rakhee.k@samsung.com'
    receivers = config.get(sect, 'email').split(",")
#    receivers = ['rakhee.k@samsung.com']
    message_txt = ""
    Subject = "File Changed"
    message_txt += "The %s was submitted in %s\n" % (file, cl)
    message = MIMEText(""" %s\n.""" % (message_txt))
    message['Subject'] = "P4 [FileLOG] %s" % file
    message['From'] = sender
    message['To'] = ", ".join(receivers)
    try:
        smtpObj = smtplib.SMTP('localhost')
        smtpObj.sendmail(sender, receivers, message.as_string())
        smtpObj.quit()
        print "Successfully sent email"
    except SMTPException:
        print "Error: unable to send email"

def getEmailFlag(cl, sect):
    files = []
    emailFlag = "false"
    fileChanged = ""
    try:
        p4.run_login()
    except P4Exception:
        for e in p4.errors:
            sys.exit(e) 
    try:
        change = p4.fetch_change(cl)
        user = change['User']
        files = config.get(sect, 'files').split(",")
        print files[1]
        client = p4.fetch_client(change['Client'])
        root = client['Root']
        logging.info("Trigger started for %s" % cl)
        files_inCl = p4.run_describe("-s", cl)
        for dict in files_inCl:
            for file in dict['depotFile']:
                if(file == files[0]):
                    emailFlag = "true"
                    print emailFlag
                    fileChanged = file
                elif(file == files[1]):
                    print files[1]
                    emailFlag = "true"
                    fileChanged = file
    except P4Exception:
        for e in p4.errors:
            print e 
    return emailFlag, fileChanged 

if  __name__ == '__main__':
    cl = sys.argv[1]
    sect = sys.argv[2]
    if(len(sys.argv) > 2):
        triggerDir = os.getcwd()
    else:
        triggerDir = "/p4/common/bin/triggers"
    logFile = "%s/%s/%s" % (triggerDir, "logs", "postSubmitEmail.log")
    logging.basicConfig(filename=logFile,filemode='a',level=logging.DEBUG,format='%(asctime)s %(levelname)s %(message)s')
    emailFlag, fileChanged = getEmailFlag(cl, sect)
    if (emailFlag == "true"):
        logging.info("%s was changed in %s" % (fileChanged, cl))
        sendEmail(fileChanged, cl, sect)
    p4.disconnect()
