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


def kill_proc():
    p.terminate()
    time.sleep(2)
    p.kill()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-qt', '--quadtarget-path', default='./QuadTarget')
    parser.add_argument('-a', '--addr', default='127.0.0.1')
    parser.add_argument('-p', '--port', default=5001)
    parser.add_argument('-o', '--output-video', default=None)
    return parser.parse_args()


ROLL = 1500
PITCH = 1500
YAW = 1500
THROTTLE = 1000
OTHERS = [1500] * 4
SLEEP = 0.1


class RCThread(threading.Thread):
    def run(self):
        local = threading.local()
        local.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        local.conn.connect((args.addr, args.port))
        local.conn.settimeout(0.0)
        while True:
            local.conn.send(multiwii.tx_generate(
                'MSP_SET_RAW_RC', *[ROLL, PITCH, YAW, THROTTLE] + OTHERS
            ))
            time.sleep(SLEEP)


if __name__ == '__main__':
    atexit.register(kill_proc)
    args = parse_args()
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((args.addr, args.port))
    conn.settimeout(0.0)
    print()
    qt_args = []
    if args.output_video is not None:
        qt_args = [args.output_video]
    p = subprocess.Popen(
        ' '.join([args.quadtarget_path] + qt_args),
        stdout=subprocess.PIPE
    )
    center = 1500.0
    bounds = 500.0
    max_dist = 20.0
    dist_scale = bounds / max_dist
    rc = RCThread()
    rc.daemon = True
    rc.start()
    while True:
        poll = p.poll()
        if poll is not None:
            break
        out = p.stdout.readline()
        p.stdout.flush()
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
                if raw_yaw < 0:
                    raw_yaw = 1300
                elif raw_yaw > 0:
                    raw_yaw = 1700
                YAW = raw_yaw
                fps = decoded['fps']
            except JSONError as e:
                print(e, out)
                continue
        sleep_time = 0.0
        # sleep_time = 0.3 - (1.0 / fps)
        # if sleep_time < 0.0 or sleep_time > 0.3:
        #     sleep_time = 0.3
        print('dist:', dist, 'p:', PITCH, 'r:', ROLL, 'y:', YAW,
              't:', THROTTLE,
              'fps:', fps, 'sleep:', sleep_time)
        # time.sleep(sleep_time)
    print()
