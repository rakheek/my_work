#!/bin/sh

list=$1

while read line; do
    echo $line    
    p4 monitor clear $line 
done < $list

