#!/usr/bin/env python

# ModuleName::calculate_lsf_ids.py
# LICENSE: APL, Samsung Research America, Mountain View, CA, 94043 USA
# __author__ = 'Hardikprasad Patel'

import sys
import os
import getopt
import subprocess
from subprocess import Popen, PIPE

if len(sys.argv) != 2:
  #print ("Please specify atleast one argument on the command line.")
  print ("Usage: %s <Arg1> <Arg2> <Arg3> ..." % sys.argv[0])
  sys.exit(1)

# Input variables from commandline arguments
abortDirPath = sys.argv[1]

# Lsf ID parser
def parse_lsf_ids(abortDirPath):
  lsf_ids = []
  currentDir = os.getcwd()
  #print ("1. The cwd is: %s" % currentDir)

  abortDir = "%s" % (abortDirPath)
  #print ("Abort dir path is: %s" % abortDir)

  try:
    os.chdir(abortDir)
    #tempDir = os.getcwd()
    #print ("TEMP >>> The cwd is: %s " % tempDir)
  except OSError as Err:
    sys.exit(Err)

  # Run subprocess command with try and except
  try:
  # command to get lsf ids on shell command
  # grep -E -L 'PASSED' *.log | while read -r x; do grep -E 'Job <|LSF ID:' "$x"; done | cut -d '<' -f2 | cut -d '>' -f1 | cut -d ' ' -f3
    cmd = "%s %s %s" % ("grep -E -L 'PASSED' *.log | while read -r x; do grep -E 'Job <|LSF ID:'", "\"$x\";", "done | cut -d '<' -f2 | cut -d '>' -f1 | cut -d ' ' -f3")
    #print ("command is: %s" % cmd)
    proc = subprocess.Popen(cmd, shell=True, stdout=PIPE)
    #stdout, err = proc.communicate()
    for line in iter(proc.stdout.readline, ''):
      lsf_ids.append(line.rstrip('\n'))
    #print lsf_ids
    for lsf_job in lsf_ids:
      #print ("Issuing bkill command to lsf job id:%s" % lsf_job)
      lsf_job_id = long(lsf_job)
      print ("Issuing bkill command to lsf job id:%ld" % lsf_job_id)
      #bkill_cmd = "%s" % ("ssh aplnd002 bkill lsf_job_id")
      bkill_cmd = "ssh aplnd002 bkill %s" % (lsf_job_id)
      bkill_proc = subprocess.Popen(bkill_cmd, shell=True, stdout=PIPE)
      stdout,err = bkill_proc.communicate()
    #lsf_ids_str = ','.join(lsf_ids)
    #print (lsf_ids_str)
  except OSError as Err:
    sys.exit(Err)

  os.chdir(currentDir)
  currentDir = os.getcwd()
  #print ("2. The cwd is: %s " % currentDir)

# Main function
def main(argv):
  parse_lsf_ids(abortDirPath)

if __name__ == "__main__":
  main(sys.argv[1:]) 
