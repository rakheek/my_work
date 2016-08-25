#!/bin/sh

reload_list=$1

while read line; do
    echo $line    
    p4 monitor terminate $line
done < $reload_list

