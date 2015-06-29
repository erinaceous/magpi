#!/bin/bash

if [ "$1" = "" ]; then
    OUTFILE="/root/recording.h264"
else
    OUTFILE="$1";
fi

# Mode 5 = 1296x730
raspivid -awb off -ex fixedfps -w 1296 -h 730 -fps 49 -b 20000000 -t 0 -n -o $OUTFILE
