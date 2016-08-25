#!/home/apps/python_org/2.7.6/bin/python

import os
import sys
import datetime
import time
from subprocess import Popen, PIPE

def clean_bkp(nfs_backup):
    print nfs_backup
    for file in os.listdir(nfs_backup):
        file = os.path.join(nfs_backup, file)
        now = time.time()
        if (os.stat(file).st_mtime < now - 10 * 86400):
            if(os.path.isfile(file)):
                print "Removing older backups %s" % file
                os.remove(file)

def create_mysql_bkp(nfs_backup):
    mysql_dir = '/var/mysql/lib'
    mysql_user = 'root'
    mysql_passwd = 'gq!j5A!rDBqU2pTo5mjV'
    ec_db = 'ecdb'
    today = datetime.date.today()
    ec_bkp = "%s_%s_%s" % ("EC", "BKP", today) 
    cmd = "%s %s %s %s%s %s %s %s %s/%s" % ("mysqldump", "-u", mysql_user, "-p", mysql_passwd, "--single-transaction", ec_db, ">", nfs_bkp, ec_bkp)
    print cmd
#    cmd2 = "%s %s %s/." % ("cp", ec_bkp, nfs_bkp)
#    print cmd2
    try:
        os.system(cmd)
    except OSError as e:
        print e 
#    try:
#        os.system(cmd2)
#    except OSError as e:
#        print e 
	
if  __name__ == '__main__':
    nfs_bkp = "/appdata/EC_BACKUP"
    create_mysql_bkp(nfs_bkp)
    clean_bkp(nfs_bkp)
