#!/bin/bash -x

if [ "$#" != "6" ]; then
   echo "Invalid number of arguments"
   exit 1
fi

platform=$1
lastGoodCL=$2
clSet=$3
template=$4
agent=$5
module=$6

if [ "$lastGoodCL" == "" ] ; then
   echo "Error: lastGood CL cannot be null"
   exit 1
fi

if [ "$platform" == "linux" ] ; then
      export P4TICKETS="/home/ecagent-stg/p4ticket1"
else 
      export P4TICKETS="C:\users\ecagent\p4tickets.txt"
fi

c_file_d="$module.txt"

p4 -u ecbuild -p apl-pstream01:2001 client -t $template -o $template-$agent > $c_file_d  
p4 -u ecbuild -p apl-pstream01:2001 client -i < $c_file_d 

p4 -u ecbuild -p apl-pstream01:2001 -c $template-$agent revert //...  
p4 -u ecbuild -p apl-pstream01:2001 -c $template-$agent sync @$lastGoodCL  


if [ "$clSet" != "" ] ; then
    for cl in $clSet; do
        echo "unshelving change $cl ..."
        p4 -u ecbuild -p apl-pstream01:2001 -c $template-$agent unshelve -s $cl -f  
    done
fi

