#!/bin/bash

while true; do
	sudo socat pty,raw,echo=0,link=/dev/ttyS1,waitslave,b115200 tcp:192.168.111.1:5001,reuseaddr &
	sleep 1
	sudo chmod 777 /dev/ttyS1
	wait
	sleep 1
done
