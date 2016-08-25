#!/bin/sh

SRK_clients=$1

while read line; do
    echo $line    
    p4 client -f -d -Fs $line
done < $SRK_clients

