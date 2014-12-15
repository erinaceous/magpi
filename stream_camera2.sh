#!/bin/bash

raspivid -t 0 -h 720 -w 1080 -fps 25 -hf -b 2000000 -o - |\
	socat stdin tcp-listen:43110
