#!/usr/bin/env python2
# vim: set tabstop=4 shiftwidth=4 textwidth=79 cc=72,79:
"""
    track_targets: Run the quadtarget program and parse the JSON data
    it outputs, use to set flight controller stick values via multiwiid.
    Original Author: Owain Jones [github.com/erinaceous] [contact@odj.me]
"""

from __future__ import print_function
import asyncproc
import argparse
import multiwii
import atexit
import socket
try:
    import simplejson as json
    JSONError = json.JSONDecodeError
except ImportError:
    try:
        import cjson as json
        json.loads = json.decode
        JSONError = json.DecodeError
    except ImportError:
        import json
        JSONError = ValueError
import time
import os


p = None


def kill_proc():
    p.kill()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-qt', '--quadtarget-path', default='./QuadTarget')
    parser.add_argument('-a', '--addr', default='127.0.0.1')
    parser.add_argument('-p', '--port', default=5001)
    parser.add_argument('-o', '--output-video', default=None)
    return parser.parse_args()


if __name__ == '__main__':
    atexit.register(kill_proc)
    args = parse_args()
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((args.addr, args.port))
    print()
    qt_args = []
    if args.output_video is not None:
        qt_args = [args.output_video]
    p = asyncproc.Process(args.quadtarget_path)
    center = 1500.0
    bounds = 500.0
    max_dist = 20.0
    dist_scale = bounds / max_dist
    while True:
        poll = p.wait(os.WNOHANG)
        if poll is not None:
            break
        out = p.read()
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
                pitch = int(center - ((raw_pitch * dist) * dist_scale))
                roll = int(center - ((raw_roll * dist) * dist_scale))
                yaw = raw_yaw
                if yaw < 0:
                    yaw = 1300
                elif yaw > 0:
                    yaw = 1700
                print(dist, pitch, roll, yaw)
                others = [1000, 1500, 1500, 1500, 1500]
                conn.send(multiwii.tx_generate(
                    'MSP_SET_RAW_RC', *[roll, pitch, yaw] + others
                ))
            except JSONError as e:
                print(e)
                print(out)
                continue
            time.sleep(0)
    print()
