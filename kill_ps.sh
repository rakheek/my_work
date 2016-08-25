#!/bin/sh

SRK_clients=$1

while read line; do
    echo $line    
    kill -9 $line
done < $SRK_clients

