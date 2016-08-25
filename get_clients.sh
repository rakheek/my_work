#!/bin/sh

list=$1

while read line; do
#    echo $line    
    p4 clients -u $line | awk '{print $2}'
done < $list

