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
import select
import serial
import socket
import time


config = __import__('configparser').ConfigParser()
config.read_file(open('/etc/magpi.ini', 'r'))
config = config['multiwiid']


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-s', '--serial-port',
        default=config.get('serial_dev'),
        help='Serial device to communicate with MultiWii over'
    )
    parser.add_argument(
        '-o', '--output-port',
        default=config.getint('listen_port'),
        help='Allow clients to connect on this TCP port'
    )
    return parser.parse_args()


def serial_config(serial_port=config.get('serial_dev')):
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
    ser.writeTimeout = 0
    return ser


def main():
    args = parse_args()
    ser = serial_config(args.serial_port)
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('0.0.0.0', args.output_port))
    srv.settimeout(0.0)
    srv.listen(0)

    clients = [srv]
    recv_buffer = 1048576  # 1KB buffer is probably overkill! Oh well

    while True:
        read_socks, write_socks, err_socks = select.select(
            clients, [], []
        )
        for sock in read_socks:
            sock.settimeout(0.0)
            if sock == srv:
                sockfd, addr = srv.accept()
                clients.append(sockfd)
                print(time.time(), "Accepted new client", addr)
            else:
                try:
                    data = sock.recv(recv_buffer)
                    if data:
                        ser.write(data)
                        s = ''
                        while True:
                            r = ser.read(recv_buffer)
                            if r in ['', None]:
                                break
                            s += r
                        if len(s) > 0:
                            sock.sendall(s)
                        ser.flush()
                        # print('<<', data)
                        # print('>>', s)
                    else:
                        sock.close()
                        clients.remove(sock)
                        print(time.time(), "Removed client")
                except Exception as e:
                    print(e)
                    sock.close()
                    clients.remove(sock)
                    print(time.time(), "Removed client")
        for sock in err_socks:
            sock.close()
            clients.remove(sock)
            print(time.time(), "Removed client")

    srv.close()

if __name__ == '__main__':
    main()
