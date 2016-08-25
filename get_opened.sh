#!/bin/sh

users=$1

while read line; do
    num_opened_files=`p4 opened -u $line | wc -l`
    echo "$num_opened_files, $line"
done < $users

