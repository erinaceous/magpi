#!/bin/bash

if [ "$1" = "" ]; then
    OUTFILE="/data/recording.h264"
else
    OUTFILE="$1";
fi

WIDTH=1296
HEIGHT=730
FPS=49
BITRATE=25000000
INTRA_REFRESH=0

# Set ionice priority to highest possible. Don't set to realtime in case we
# freeze the Pi / stop it from being able to write telemetry to SD.
# Try and buffer the output a bit more too by piping to file rather than
# letting raspivid write directly to it.
# Also enable -ih (inline headers) so we get timing information!

ionice -c 1 -n 1 raspivid -vf -awb off -ex fixedfps -ISO 100 -drc high -ih \
    -g $INTRA_REFRESH -pf high -v \
    -w $WIDTH -h $HEIGHT -fps $FPS -b $BITRATE -t 0 -n -o $OUTFILE
sync
