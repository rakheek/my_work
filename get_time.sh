#!/bin/bash

host=$1

cur_time=`/usr/sbin/ntpq -p`
echo "$host has $cur_time"
