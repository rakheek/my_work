#!/bin/sh

SRK_clients=$1

while read line; do
    echo $line    
    p4 user -f -d $line
done < $SRK_clients

