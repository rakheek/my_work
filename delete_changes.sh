#!/bin/sh

SRK_clients=$1

while read line; do
    echo $line    
    p4 change -f -d $line
done < $SRK_clients

