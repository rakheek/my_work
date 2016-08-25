#!/bin/sh
# Checks templates against saved files to make sure they are up to date
tmp=`mktemp -d`
this=`dirname $0`
this=`cd $this;pwd`
for t in `p4 clients -e '*template*' | awk '{print $2}'`; do 
    p4 client -o $t > $tmp/$t;
    diff -q -I '---' -I 'Access\|Update' $t $tmp/$t > /dev/null || echo $t
done

rm -rf $tmp
