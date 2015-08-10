#!/bin/bash

VIDEO_FILE=""
if [ "$1" != "" ]; then
    VIDEO_FILE="-o $1"
fi

export QUADTARGET_CONFIG=/root/quadtargetfsm/build/config.ini
cd /root/magpi
python2 ./track_targets.py -qt /root/quadtargetfsm/build/QuadTarget $VIDEO_FILE
