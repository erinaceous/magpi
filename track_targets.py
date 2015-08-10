#!/usr/bin/env python2
# vim: set tabstop=4 shiftwidth=4 textwidth=79 cc=72,79:
"""
    track_targets: Run the quadtarget program and parse the JSON data
    it outputs, use to set flight controller stick values via multiwiid.
    Original Author: Owain Jones [github.com/erinaceous] [contact@odj.me]
"""

from __future__ import print_function
import subprocess
import threading
import argparse
import multiwii
import atexit
import socket
import select
try:
    import cjson as json
    json.loads = json.decode
    JSONError = json.DecodeError
except ImportError:
    import json
    JSONError = ValueError
    print('Warning: cjson module not found. Defaulting to slooow parser.')
import time
import os


p = None
conn = None
rc = None


ROLL = 1500
PITCH = 1500
YAW = 1500
THROTTLE = 1000
MAX_THROTTLE = 1700
AUX1 = 1500
AUX2 = 1500
AUX3 = 1500
AUX4 = 1500
SLEEP = 0.1


def set_armed(arm=False):
    global ROLL, PITCH, YAW, THROTTLE, AUX1, AUX2, AUX3, AUX4, SLEEP
    ROLL = 1500
    PITCH = 1500
    YAW = 1500
    AUX1 = 1500
    AUX2 = 1500
    AUX3 = 1500
    AUX4 = 1500
    if arm:
        print(time.time(), 'arming')
        yaw_val = 2000
    else:
        print(time.time(), 'disarming')
        yaw_val = 1000
    if not arm:
        while THROTTLE > 1000:
            THROTTLE -= 10
            conn.send(multiwii.tx_generate('MSP_SET_RAW_RC',
                *[1500, 1500, 1500, THROTTLE, AUX1, AUX2, AUX3, AUX4]
            ))
            time.sleep(0.1)
    for i in range(0, 12):
        conn.send(multiwii.tx_generate('MSP_SET_RAW_RC',
            *[1500, 1500, yaw_val, 1000, AUX1, AUX2, AUX3, AUX4]
        ))
        time.sleep(0.1)


def kill_proc():
    p.terminate()
    rc.stop()
    set_armed(False)
    time.sleep(2)
    p.kill()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-qt', '--quadtarget-path', default='./QuadTarget')
    parser.add_argument('-a', '--addr', default='127.0.0.1')
    parser.add_argument('-p', '--port', default=5001)
    parser.add_argument('-o', '--output-video', default=None)
    return parser.parse_args()


class RCThread(threading.Thread):
    def run(self):
        self.running = True
        local = threading.local()
        local.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        local.conn.connect((args.addr, args.port))
        local.conn.settimeout(0.0)
        while self.running:
            local.conn.send(multiwii.tx_generate('MSP_SET_RAW_RC',
                *[ROLL, PITCH, YAW, THROTTLE, AUX1, AUX2, AUX3, AUX4]
            ))
            time.sleep(SLEEP)

    def stop(self):
        self.running = False


if __name__ == '__main__':
    # Make sure we clean up safely. In this case, if python throws any
    # unhandled exceptions, we want to disarm the 'copter before
    # quitting.
    atexit.register(kill_proc)

    args = parse_args()

    # Configure socket connection to multiwiid
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((args.addr, args.port))
    conn.settimeout(0.0)

    # Set up the QuadTarget process
    print()
    qt_args = []
    if args.output_video is not None:
        qt_args = [args.output_video]
    p = subprocess.Popen(
        ' '.join([args.quadtarget_path] + qt_args),
        stdout=subprocess.PIPE
    )

    # Values for scaling
    center = 1500.0
    bounds = 500.0
    max_dist = 20.0
    dist_scale = bounds / max_dist

    # Set up thread for sending RC commands. This is needed so we can
    # send commands at a constant rate regardless of QuadTarget's
    # framerate.
    rc = RCThread()
    rc.daemon = True

    # Arm copter. For safety right now this actually disarms it
    set_armed(False)

    # Smoothly ramp up to maximum throttle
    while THROTTLE < MAX_THROTTLE:
        THROTTLE += 20
        conn.send(multiwii.tx_generate('MSP_SET_RAW_RC',
            *[1500, 1500, 1500, THROTTLE, AUX1, AUX2, AUX3, AUX4]
        ))
        time.sleep(0.1)

    # Enable horizon mode (AUX1 set to high), mag and gps hold modes
    AUX1 = 2000
    AUX3 = 2000
    AUX4 = 2000

    # Start the RC thread. Now it has full control of the sticks, until
    # throttle reaches minimum value.
    rc.start()

    # Sleep a little while to allow copter to climb some more at high throttle
    # Then enable baro hold mode.
    time.sleep(2)
    AUX2 = 2000

    while THROTTLE > 1150:

        # Check whether QuadTarget process is still running
        poll = p.poll()
        if poll is not None:
            break

        # Clear QuadTarget output, so that we'll get the newest data.
        p.stdout.flush()

        # Read JSON data from QuadTarget and decode it.
        out = p.stdout.readline()
        if out != "":
            try:
                decoded = json.loads(out)
                dist = 1.0
                if 'target' in decoded and decoded['target'] is not None:
                    dist = float(decoded['target']['distance(m)'])
                if dist > max_dist:
                    dist = max_dist
                if dist < 1:
                    dist = 1.0
                raw_pitch = 0.5 - (1.0 - decoded['sticks']['pitch'])
                raw_roll = 0.5 - decoded['sticks']['roll']
                raw_yaw = decoded['sticks']['yaw']
                PITCH = int(center - ((raw_pitch * dist) * dist_scale))
                ROLL = int(center - ((raw_roll * dist) * dist_scale))
                THROTTLE -= 1.0 / dist
                if raw_yaw < 0:
                    raw_yaw = 1300
                elif raw_yaw > 0:
                    raw_yaw = 1700
                YAW = raw_yaw
                fps = decoded['fps']
            except JSONError as e:
                print(e, out)
                continue

        # Report current state.
        print('dist: %0.3f' % dist, 'p:', PITCH, 'r:', ROLL, 'y:', YAW,
              't:', THROTTLE, 'fps: %0.3f' % fps, '    ', end='\r')
    print()

    # Disarm copter
    rc.stop()
    set_armed(False)

    print(time.time(), 'bye')
