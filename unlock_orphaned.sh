#!/bin/sh

orphaned_list=$1

while read line; do
    echo $line    
    p4 unlock -x $line 
done < $orphaned_list

