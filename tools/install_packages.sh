#!/bin/bash

pacman -Syu
pacman -S wireless_tools avahi socat aircrack-ng python2 python2-pip git mercurial python2-pyserial nss-mdns rng-tools hostapd dnsmasq cmake cmake-extra-modules opencv boost make gcc mosh f2fs-tools usb_modeswitch usbutils vnstat ppp wget watchdog
python2 -m easy_install strconv configparser
systemctl enable rngd
systemctl enable avahi-daemon
systemctl enable hostapd
systemctl enable dnsmasq
systemctl enable multiwii-raw
systemctl enable vnstat
systemctl enable watchdog
# systemctl enable network-wireless-adhoc@wlan0

echo "en_GB.UTF-8" >> /etc/locale.gen
locale-gen
localectl set-locale LANG=en_GB.UTF-8

# Replace hosts: line in /etc/nsswitch.conf with:
echo "hosts: files mdns_minimal [NOTFOUND=return] dns myhostname" >> /etc/nsswitch.conf

# Enable Pi-cam
echo "gpu_mem=256" >> /boot/config.txt
echo "start_file=start_x.elf" >> /boot/config.txt
echo "fixup_file=fixup_x.elf" >> /boot/config.txt
echo "turbo_mode=1" >> /boot/config.txt
echo "disable_camera_led=1" >> /boot/config.txt
echo "bcm2835-v4l2" >> /etc/modules-load.d/raspberrypi.conf

# Enable watchdog module, so we can recover from hard crashes
echo "bcm2708-wdog" >> /etc/modules-load.d/raspberrypi.conf

# Also enable 1.2A max current draw from USB- YOU WILL NEED A GOOD
# POWER SUPPLY FOR THIS, THAT CAN SUPPLY >2A STABLY.
echo "max_usb_current=1" >> /boot/config.txt

# And set the power LED to "heartbeat" mode, which will give us a CPU
# load indicator.
echo "pwr_led_trigger=heartbeat" >> /boot/config.txt

# Rename quad :)
echo "smokey.odj.me" > /etc/hostname

# Update dnsmasq
echo "interface=wlan0" >> /etc/dnsmasq.conf
echo "bind-interfaces" >> /etc/dnsmasq.conf
echo "dhcp-range=192.168.111.50,192.168.111.100,24h" >> /etc/dnsmasq.conf

# Update hostapd
echo "ssid=smokey" >> /etc/hostapd/hostapd.conf # Change to desired ssid
echo "interface=wlan0" >> /etc/hostapd/hostapd.conf
echo "hw_mode=g" >> /etc/hostapd/hostapd.conf
echo "channel=1" >> /etc/hostapd/hostapd.conf # Change to best channel for you
echo "auth_algs=1" >> /etc/hostapd/hostapd.conf
echo "wmm_enabled" >> /etc/hostapd/hostapd.conf

# Disable relatime on root partition
echo "/dev/mmcblk0p3 / ext4 defaults,rw,noatime,data=ordered 0 0" >> /etc/fstab

# Enable /data partition if it exists
echo "/dev/mmcblk0p4 /data f2fs defaults,rw,noatime 0 0" >> /etc/fstab

# Stop systemd-journald from writing to file
echo "Storage=none" >> /etc/systemd/journald.conf

# Download and install sakis3g
wget "http://www.sakis3g.com/downloads/sakis3g.tar.gz" -O sakis3g.tar.gz
tar -xzvf sakis3g.tar.gz
chmod +x sakis3g
mv sakis3g /usr/bin
