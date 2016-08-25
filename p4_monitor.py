#!/mntdir/apps/python_org/2.7.6/bin/python

import os
import re
import sys
import argparse
from P4 import P4, P4Exception
from pprint import pprint
import smtplib
from smtplib import SMTPException
from email.mime.text import MIMEText
import ConfigParser
import datetime
import subprocess
from subprocess import Popen, PIPE


config = ConfigParser.ConfigParser()
config.read('config.ini')

p4=P4()

p4.port = 'aplp4:2001'
p4.user = 'p4scripts'
p4.password = 'p4adminuser'

p4.connect()

#parser = argparse.ArgumentParser(description = 'script to get shelved CLs matching description by queue')
#parser.add_argument('--queue_type', type=str, help='hw/sw', required=True)
#args = parser.parse_args()

def send_email(commands):
    sender = 'rakhee.k@samsung.com'
    receivers = ['rakhee.k@samsung.com', 'balachandr.r@samsung.com', 'b.hoenig@samsung.com', 'v.sharayenko@samsung.com', 'w.olejowski@samsung.com', 'keshavan.v@samsung.com', 'hy10.kim@samsung.com', 'janghwan.tae@samsung.com', 'm.diarra@partner.samsung.com', 'j.reddy@partner.samsung.com', 'giri.u@partner.samsung.com', 'p.bruce@partner.samsung.com']
#    receivers = ['rakhee.k@samsung.com']
    message_txt = ""
    Subject = "List of long sync"
    for command in commands: 
        message_txt += "%s\t%s\t%s\t%s\t%s\t%s\n" % (command['id'], command['user'], command['client'], command['time'], command['command'], command['args'])
    print message_txt
    message = MIMEText("""This is the list of culprit commands\n\n %s.
            """ % (message_txt))
    message['Subject'] = "List of commands overloading Perforce server"
    message['From'] = sender
    message['To'] = ", ".join(receivers)
    try:
        smtpObj = smtplib.SMTP('localhost')
        smtpObj.sendmail(sender, receivers, message.as_string())         
        smtpObj.quit()
        print "Successfully sent email"
    except SMTPException:
        print "Error: unable to send email"

def saveListToFile(commands):
    outFile = open('/home/perforce/replica_monitor/culprit_commands.txt', 'a')
    cur_time = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
    for command in commands:
        commandString = "%s, %s, %s, %s, %s, %s, %s\n" % (cur_time, command['id'], command['user'], command['client'], command['time'], command['command'], command['args'])
        outFile.write(commandString)

def get_p4ServerUsers():
    culprit_commands = []
    culprit_users = []
    try:
        p4.run_login()
        output = p4.run("monitor", "show", "-ale")
#        output = [{'status': 'R', 'args': '/home/aziaja/Workspaces/sgpu/main/...#head', 'host': '106.120.61.25', 'client': 'aziaja_linux_sgpu', 'command': 'sync', 'user': 'a.ziaja', 'time': '03:44:07', 'prog': 'P4V/LINUX26X86_64/2014.3/1007540/v77', 'id': '1309'}, {'status': 'R', 'args': 'e:\\P4V\\apl\\...#head', 'host': '107.108.52.157', 'client': 'apl_latest_E', 'command': 'sync', 'user': 'jani.sk', 'time': '01:45:08', 'prog': 'P4V/NTX64/2014.2/973065/v77', 'id': '3869'}, {'status': 'R', 'args': '/home/pmiecielica/p4-workspaces/repo/escher/sgpu/prototype/...#head', 'host': '106.120.61.32', 'client': 'p.miecielica_tools_prototype_Linux', 'command': 'sync', 'user': 'p.miecielica', 'time': '01:43:16', 'prog': 'P4V/LINUX26X86_64/2014.2/985932/v77', 'id': '4449'}, {'status': 'R', 'args': '-f /home/mzient/Perforce/SGPU/apl/tests/apps/GFXBench/3.0/buffers/occlusion_query_results#head /home/mzient/Perforce/SGPU/apl/tests/apps/GFXBench/3.0/buffers/tf_0ms_1#head /home/mzient/Perforce/SGPU/apl/tests/apps/GFXBench/3.0/buffers/tf_0ms_2#head /home/mzient/Perforce/SGPU/apl/tests/apps/GFXBench/3.0/buffers/tf_0ms_3#head /home/mzient/Perforce/SGPU/apl/tests/apps/GFXBench/3.0/buffers/tf_0ms_4#head (14130) /home/mzient/Perforce/SGPU/apl/tests/apps/GFXBench/3.0/buffers/tf_31170ms_6#head', 'host': '106.120.61.24', 'client': 'mzient_APL_SRPOL_Linux', 'command': 'sync', 'user': 'm.zientkiewi', 'time': '01:29:33', 'prog': 'P4V/LINUX26X86_64/2014.3/998867/v77', 'id': '11323'}, {'status': 'R', 'args': '/home/mzient/Perforce/SGPU/apl/extern/...#head', 'host': '106.120.61.24', 'client': 'mzient_APL_SRPOL_Linux', 'command': 'sync', 'user': 'm.zientkiewi', 'time': '01:29:26', 'prog': 'P4V/LINUX26X86_64/2014.3/998867/v77', 'id': '11432'}] 
        for list in output:
            if re.search("sync", list['command']):
                if (list['time'] > "00:40:10"):
#                if re.search("IDLE", list['command']) or re.search("verify", list['command']) or re.search("rmt-Journal", list['command']) or re.search("status", list['command']) or re.search("client", list['command']):
#                    pass
#                else:
                    culprit_commands.append(list)
                    culprit_users.append(list['user'])
    except P4Exception:
        for e in p4.errors:
            sys.exit(e) 
    return culprit_commands, culprit_users

if  __name__ == '__main__':
    commands, users = get_p4ServerUsers()
    pprint(commands)
    saveListToFile(commands)
    pprint(users)
    if len(commands) > 0:
        send_email(commands)
    print len(commands)
    p4.disconnect()
