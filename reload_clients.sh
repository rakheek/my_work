#!/bin/sh

reload_list=$1

while read line; do
    echo $line    
    p4 reload -f -c $line -p pal-apl1:2001
done < $reload_list

