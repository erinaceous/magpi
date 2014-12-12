#!/bin/bash

if [ "`whoami`" != "root" ]; then
	dialog --msgbox "This script needs to be ran as root! Try 'sudo' or 'sudo -s'" 10 40
	exit 1
fi

dialog --inputbox "Enter the name of your drone. This will be the drone's hostname, and also the name of the wireless network." 12 40 `hostname` 2>/etc/hostname

ADHOC_IFACE="`cat /etc/adhoc_iface`"
if [ "$ADHOC_IFACE" = "" ]; then
	ADHOC_IFACE="wlan0"
fi
dialog --inputbox "Enter the network interface you want to run the wireless network on (It's probably wlan0)" 12 40 "$ADHOC_IFACE" 2>/etc/adhoc_iface

ADHOC_IP="`ip addr show dev $ADHOC_IFACE | fgrep 'inet ' | awk '{ print $2 }' | cut -d '/' -f 1`"
if [ "$ADHOC_IP" = "" ]; then
	ADHOC_IP="`cat /etc/adhoc_ip`"
fi
dialog --inputbox "Enter the IPv4 address you want your drone to have on it's wireless network (x.x.x.x)" 12 40 "$ADHOC_IP" 2>/etc/adhoc_ip
sync
dialog --msgbox "Finished configuring! Make sure your MultiWii board and USB wireless dongle are connected via USB, then restart your Pi. When it boots back in, you should be able to connect to the '`hostname`' Ad-Hoc wireless network and SSH in via `cat /etc/adhoc_ip`." 18 40
