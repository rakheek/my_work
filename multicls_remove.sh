#!/bin/sh

Pending_cls=$1

while read line; do
    echo $line    
    p4 shelve -f -d -c $line
    p4 change -f -d $line
    done < $Pending_cls
            
