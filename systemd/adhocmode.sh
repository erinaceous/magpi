#!/bin/bash

ifconfig wlan0 down  # disable if up
iw reg set BO  # more transmit power
ifconfig wlan0 up
iwconfig wlan0 mode ad-hoc
iwconfig wlan0 txpower 1000mW
iwconfig wlan0 essid magpi
iwconfig wlan0 commit
ifconfig wlan0 192.168.125.1
