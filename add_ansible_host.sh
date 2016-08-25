#!/bin/sh

new_hosts=$1

while read line; do
    echo $line    
    ansible $line -m raw -a id
done < $new_hosts

