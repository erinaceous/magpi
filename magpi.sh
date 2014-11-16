#!/bin/bash

PIDFILE=/tmp/magpi.pid

function start() {
	stop
	cd /home/owain/magpi
	./read_telemetry.py > /var/log/magpi.last 2>&1 &
	PID=$!
	echo $PID > $PIDFILE
	echo "Started with PID $PID. Recorded in $PIDFILE."
}

function stop() {
	if [ -f "$PIDFILE" ]; then
		echo "Process `cat $PIDFILE` found. Terminating..."
		kill -s TERM `cat $PIDFILE`
		rm $PIDFILE
	fi
}

function stop_force() {
	if [ -f "$PIDFILE" ]; then
		echo "Process `cat $PIDFILE` found. Killing..."
		kill -s KILL `cat $PIDFILE`
		rm $PIDFILE
	fi
}

if [ "$1" != "" ]; then
	$1;
fi
