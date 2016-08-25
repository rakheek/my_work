#!/bin/bash
#source /home/perforce/.bashrc
server="pal-apl1"
count="1"
for data in $server
do
        command=$(ssh $data "p4 pull -lj" |head -2 | sed 's/\,//g'|sed 's/\.//g' |  awk '{print $9}'| pr -at2)
	IFS=" "
	set $datavar
	replicaValue=${1:0:4}
	masterValue=${2:0:4}
	if [ $masterValue==$replicaValue ] ; then
                status=0
                statustxt=OK
        elif [ $masterValue > $replicaValue ]; then
                status=2
                statustxt=CRITICAL
        else
		        status=1
                statustxt=WARNING
        fi
        echo "$status replica_$server count=$count; $statustxt - $count P4Replicat $statustxt $server: $command"| /bin/sed 's/^/"/;s/$/"/'| /bin/sed 's/^/echo /' > /usr/lib/check_mk_agent/local/pal-apl1-replica
done
