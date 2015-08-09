#!/usr/bin/env python2
# vim: set tabstop=4 shiftwidth=4 textwidth=79 cc=72,79:
"""
    get_targets: Run the quadtarget program and parse the JSON data
    it outputs (example of how to use the program from python code)
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
    parser.add_argument('-o', '--output-video', default=None)
    return parser.parse_args()


if __name__ == '__main__':
    atexit.register(kill_proc)
    args = parse_args()
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect(('127.0.0.1', 5001))
    print()
    p = asyncproc.Process(args.quadtarget_path)
    while True:
        poll = p.wait(os.WNOHANG)
        if poll is not None:
            break
        out = p.read()
        if out != "":
            try:
                decoded = json.loads(out)
                pitch = int(1300 + (decoded['sticks']['pitch'] * 400))
		roll = int(1300 + (decoded['sticks']['roll'] * 400))
		others = [1500, 1000, 1500, 1500, 1500, 1500]
                conn.send(multiwii.tx_generate(
			'MSP_SET_RAW_RC', *[roll, pitch] + others
		))
            except JSONError as e:
                print(e)
                print(out)
                continue
            time.sleep(0)
    print()
