#!/bin/bash

raspivid -w 1280 -h 1024 -fps 25 -b 100000000 -t 0 -n -o - |\
    tee -a record.h264 |\
    socat stdin udp-sendto:192.168.125.2:5001
