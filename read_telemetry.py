#!/usr/bin/env python2
# vim: set tabstop=4 shiftwidth=4 textwidth=79 cc=72,79:
"""
    read_telemetry: Read useful data from MultiWii board in a fast loop.
                    saves to disk as gzipped CSV files. Also sends data
                    in a UDP broadcast.
    Original Author: Owain Jones [github.com/erinaceous] [contact@odj.me]
"""
# TODO: Python3-ize

from __future__ import print_function
from collections import OrderedDict
import argparse
import readline
import multiwii
import strconv
import config
import serial
import struct
import socket
import gzip
import time
import sys


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--header-every', type=int,
                        default=config.HEADER_EVERY,
                        help='Broadcast data header every N broadcasts')
    parser.add_argument('-n', '--name', default=config.NAME,
                        help='Name/ID of quadcopter.')
    parser.add_argument('-s', '--serial-port', default=config.SERIAL_PORT,
                        help='Serial port to communicate with MultiWii over')
    parser.add_argument('-l', '--log', default=config.THINGS_TO_LOG,
                        help='Comma-delimited list of serial commands to run')
    parser.add_argument('-o', '--output', default=config.DATA_FILE,
                        help='File to put CSV output in. Can also gzip files.')
    parser.add_argument('-i', '--interactive', default=False,
                        action='store_true')
    parser.add_argument('-p', '--udp-port', type=int, default=config.UDP_PORT)
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


def get_packet(ser, name, wait_time=config.CMD_WAIT_TIME):
    ser.write(multiwii.get_command(name))
    time.sleep(wait_time)
    s = ser.readall()
    return multiwii.rx_parse(name, s)


def get_multiple_packets(ser, names, wait_time=config.CMD_WAIT_TIME):
    ser.write(''.join([multiwii.get_command(name) for name in names]))
    time.sleep(wait_time)
    output = OrderedDict()
    for name in names:
        l = multiwii.get_response_length(name)
        s = ser.read(l)
        output[name] = multiwii.rx_parse(name, s)
    return output


def send_multiple_packets(ser, datas, wait_time=config.CMD_WAIT_TIME):
    packets = ''
    for data in datas:
        data = data.strip().split(' ')
        cmd = data[0]
        packet = multiwii.tx_generate(cmd,
                                      *[strconv.convert(d) for d in data[1:]])
        packets += packet
        print('|', cmd, packet.encode('hex'))
    ser.write(packets)
    time.sleep(wait_time)
    print('<', ser.readall())


def pretty_str(packet):
    i = 0
    l = len(packet.keys()) - 1
    end = ', '
    for key, value in packet.iteritems():
        i += 1
        if i == l:
            end = ';\n'
        if key.startswith('_') is False:
            print('%s:' % key, value, end=end)


def main():
    try:
        readline.read_history_file()
    except IOError:
        pass
    import atexit
    atexit.register(readline.write_history_file)

    args = parse_args()
    ser = serial_config(args.serial_port)

    if args.udp_port is not -1:
        cs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        cs.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    if args.output is not None:
        args.output = args.output.format(timestamp=str(time.time()),
                                         name=args.name)
        if args.output.endswith('.gz'):
            outfile = gzip.open(args.output, 'w+', 9)
        else:
            outfile = open(args.output, 'w+')
    else:
        outfile = open('/dev/null', 'a+')

    for i in range(config.RESET_WAIT_SECS, 0, -1):
        print('Waiting for MultiWii board to reload... %02d' % i, end='\r')
        sys.stdout.flush()
        time.sleep(1)
    print('-' * 79)

    frame = 0
    wait_time = config.CMD_WAIT_TIME
    nErrs = 0
    header_written = False
    while True:
        if args.interactive:
            prompt = input('> ')
        if nErrs > 1:
            wait_time += 0.01
            nErrs = 0
        if args.interactive and prompt is not '':
            try:
                if prompt.lower() in ['exit', 'quit']:
                    raise SystemExit
                send_multiple_packets(ser, prompt.strip().split(','),
                                      wait_time)
            except KeyError:
                print('Invalid command')
            except struct.error as e:
                print('Invalid arguments to command (not enough?)')
                print(e)
        try:
            frame += 1
            timestamp = time.time()
            data = get_multiple_packets(ser, args.log.split(','), wait_time)
            data['packet'] = {'frame': frame, 'timestamp': timestamp,
                              'wait_time': wait_time}
            if args.interactive:
                for key, value in data.iteritems():
                    print(key, end=' ')
                    pretty_str(value)
            if header_written is False:
                print(timestamp, 'First data acquired! Headers:')
                header = ','.join(sum([['%s_%s' % (key.replace('MSP_', ''),
                                                   keykey) for keykey in
                                   data[key] if keykey.startswith('_')
                                   is False] for key in data.keys()], []))
                print(header)
                print(header, file=outfile)
                header_written = True
            if header_written is True:
                data = ','.join(sum([[str(val) for keykey, val
                                     in data[key].iteritems()
                                     if keykey.startswith('_') is False]
                                    for key in data.keys()], []))
                if args.udp_port is not -1:
                    if frame % args.header_every == 0:
                        cs.sendto('$MAGPI[%s]_H,' % args.name + header + '\n',
                                  ('255.255.255.255', args.udp_port))
                    cs.sendto('$MAGPI[%s]_D,' % args.name + data + '\n',
                              ('255.255.255.255', args.udp_port))
                print(data, file=outfile)
            nErrs = 0
        except multiwii.Command.ChecksumError as e:
             nErrs += 1
             print(timestamp, e)
        except multiwii.Command.NotACommand as e:
            nErrs += 1
            print(timestamp, e)
        if args.interactive:
            print('-' * 79)
        ser.readall()
        time.sleep(0)


if __name__ == '__main__':
    main()
