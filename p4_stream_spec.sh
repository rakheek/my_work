#!/bin/sh

stream_spec=$1

while read line; do
    owner=`p4 stream -o $line |grep -i "Owner:" | grep -v "#"`
    unlocked_stream=`p4 stream -o $line | grep unlocked`
    if [ "$?" == 0 ]; then
        echo "$line is unlocked and is owned by $owner"
    fi
done < $stream_spec

