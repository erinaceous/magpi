#!/usr/bin/env python2
# vim: set tabstop=4 shiftwidth=4 textwidth=79 cc=72,79:
"""
    test_controller: Sends fake RC stick commands to multiwiid.
    Original Author: Owain Jones [github.com/erinaceous] [contact@odj.me]
"""
# TODO: Python3-ize

from __future__ import print_function
import argparse
import multiwii
import config
import socket
import time


recv_buffer = 1048576


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--input-port', default=config.OUTPUT_PORT,
                        help='Port to communicate with multiwiid over')
    return parser.parse_args()


def socket_config(socket_port=config.OUTPUT_PORT):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', socket_port))
    return sock


if __name__ == '__main__':
    conn = socket_config()
    i = 0
    while True:
        conn.send(multiwii.tx_generate(
            'MSP_SET_RAW_RC', *[1000 + (i % 1000)] * 8
        ))
        i += 1
        time.sleep(0.1)
