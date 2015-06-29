#!/usr/bin/env python2
# vim: set tabstop=4 shiftwidth=4 textwidth=79 cc=72,79:
"""
    multiwiid: A simple one-to-many serial multiplexer. Clients can send
    commands to and from the serial device by talking to this process over
    a TCP UNIX socket.

    ANY DATA RECEIVED FROM THE SERIAL DEVICE WILL BE SENT TO ALL CONNECTED
    CLIENTS.

    Original Author: Owain Jones [github.com/erinaceous] [contact@odj.me]
"""
# TODO: Python3-ize

from __future__ import print_function
import argparse
import config
import select
import serial
import socket


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--serial-port', default=config.SERIAL_PORT,
                        help='Serial port to communicate with MultiWii over')
    parser.add_argument('-o', '--output-socket', default=config.OUTPUT_SOCKET,
                        help='Path to UNIX socket to create')
    return parser.parse_args()


def serial_config(serial_port=config.SERIAL_PORT):
    # Thanks to
    # http://www.calvin.edu/academic/engineering/2013-14-team8/code/final/MultiWii_Telemetry_RevH.py.tmp20140503-19-1pkuhii
    # who I copy-pasted this block from, saving me a bunch of time
    # figuring out why my serial wasn't working :)
    ser = serial.Serial(serial_port)
    ser.baudrate = 115200
    ser.bytesize = serial.EIGHTBITS
    ser.parity = serial.PARITY_NONE
    ser.stopbits = serial.STOPBITS_ONE
    ser.timeout = 0
    ser.xonxoff = False
    ser.rtscts = False
    ser.dsrdtr = False
    ser.writeTimeout = 2
    return ser


def main():
    args = parse_args()
    ser = serial_config(args.serial_port)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(args.output_socket)
    srv.listen(5)

    clients = [srv]
    recv_buffer = 4096

    while True:
        read_socks, write_socks, err_socks = select.select(
            clients, [], []
        )
        for sock in read_socks:
            if sock == srv:
                sockfd, addr = srv.accept()
                clients.append(sockfd)
            else:
                try:
                    data = sock.recv(recv_buffer)
                    if data:
                        ser.write(data)
                        time.sleep(config.CMD_WAIT_TIME)
                        s = ser.read()
                        sock.send(s)
                except:
                    sock.close()
                    clients.remove(sock)

    srv.close()

if __name__ == '__main__':
    main()
