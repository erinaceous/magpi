#!/bin/bash

raspivid -w 1280 -h 720 -fps 60 -b 100000000 -t 0 -n -o recording.h264
