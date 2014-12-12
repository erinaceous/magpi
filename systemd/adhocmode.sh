#!/bin/bash

DEFAULT_IFACE="wlan0"
DEFAULT_IP="192.168.125.1"

if [ -f /etc/adhoc_ip ]; then
	IP="`cat /etc/adhoc_ip`"
else
	IP="$DEFAULT_IP"
fi

if [ -f /etc/adhoc_iface ]; then
	IFACE="`cat /etc/adhoc_iface`"
else
	IFACE="$DEFAULT_IFACE"
fi

ifconfig $IFACE down  # disable if up
ifconfig $IFACE up
iwconfig $IFACE mode ad-hoc
iwconfig $IFACE txpower 1000mW
iwconfig $IFACE essid `hostname`
iwconfig $IFACE commit
ifconfig $IFACE $IP
