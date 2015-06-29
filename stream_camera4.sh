#!/bin/bash

raspivid -w 1280 -h 720 -fps 25 -b 100000000 -t 0 -n -o - |\
    tee recording.h264 |\
    socat stdin udp-sendto:169.254.10.182:5001
