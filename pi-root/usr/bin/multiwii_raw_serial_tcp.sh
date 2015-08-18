#!/bin/bash

source /etc/conf.d/multiwii

while true; do
	socat tcp-listen:$MW_TCP_PORT,reuseaddr file:$MW_SERIAL_PORT,raw,echo=0,b$MW_SERIAL_BAUD
	sleep 1
done
