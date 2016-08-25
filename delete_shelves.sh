#!/bin/sh

list=$1

while read line; do
    echo $line    
    p4 shelve -f -d -c $line 
done < $list

