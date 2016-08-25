#!/bin/bash

if [ $# -ne 3 ]; then
  # TODO: print usage
  echo "provide 3 argumens as : 1). Platform, 2)clList, 3). Workspace Path"
  exit 1
fi

platform=$1
cls_list=$2
ws_path=$3

echo "Platform is: $platform"
echo "Cl list is: $cls_list"
echo "The workspace path is: $ws_path"

if [ "$platform" == "linux" ] ; then
  export P4TICKETS="/home/ecagent/p4ticket"
else
  export P4TICKETS="C:\users\ecagent\p4tickets.txt"
fi

IFS=','

cd $ws_path
for cl in $cls_list
  do
    output=`p4 -u ecbuild -p aplp4:2001 files @=${cl} | grep -i "\- add" | cut -d'#' -f1 | cut -d'/' -f5-`
    #echo $output
    
    f_output=`echo "${output//$'\n'/$','}"`
    #echo $f_output

    for line in $f_output
      do
        #echo $line
        if [ -f "$line" ]; then
          echo "file exists. Deleting $line"
            rm -f $line
        fi
      done
  done
#cd -
