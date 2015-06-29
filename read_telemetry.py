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
import subprocess
import argparse
import readline
import multiwii
import strconv
import config
import struct
import socket
import array
import gzip
import time
import sys


recv_buffer = 1048576


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--header-every', type=int,
                        default=config.HEADER_EVERY,
                        help='Broadcast data header every N broadcasts')
    parser.add_argument('-n', '--name', default=config.NAME,
                        help='Name/ID of quadcopter.')
    parser.add_argument('-t', '--input-port', default=config.OUTPUT_PORT,
                        help='Port to communicate with multiwiid over')
    parser.add_argument('-l', '--log', default=config.THINGS_TO_LOG,
                        help='Comma-delimited list of serial commands to run')
    parser.add_argument('-o', '--output', default=config.DATA_FILE,
                        help='File to put CSV output in. Can also gzip files.')
    parser.add_argument('-i', '--interactive', default=False,
                        action='store_true')
    parser.add_argument('-p', '--udp-port', type=int, default=config.UDP_PORT)
    parser.add_argument('--video', default=config.VIDEO_FILE)
    return parser.parse_args()


def socket_config(socket_port=config.OUTPUT_PORT):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', socket_port))
    return sock


def get_packet(sock, name, wait_time=config.CMD_WAIT_TIME):
    sock.send(multiwii.get_command(name))
    s = sock.recv(recv_buffer)
    return multiwii.rx_parse(name, s)


def get_multiple_packets(sock, names, wait_time=config.CMD_WAIT_TIME):
    sock.send(b''.join([multiwii.get_command(name) for name in names]))
    output = OrderedDict()
    # input = array.array('c', sock.recv(recv_buffer))
    input = sock.recv(recv_buffer).split('$M>')
    if input[0] == '':
        input.remove(input[0])
    for i, name in enumerate(names):
        l = multiwii.get_response_length(name)
        s = b'$M>' + input[i]
        output[name] = multiwii.rx_parse(name, s)
    return output


def send_multiple_packets(sock, datas, wait_time=config.CMD_WAIT_TIME):
    packets = ''
    for data in datas:
        data = data.strip().split(' ')
        cmd = data[0]
        packet = multiwii.tx_generate(cmd,
                                      *[strconv.convert(d) for d in data[1:]])
        packets += packet
        print('|', cmd, packet.encode('hex'))
    sock.send(packets)
    print('<', sock.recv(recv_buffer))


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


cam_proc = None


def at_exit():
    readline.write_history_file()
    if cam_proc is not None:
        cam_proc.terminate()


def main():
    try:
        readline.read_history_file()
    except IOError:
        pass
    import atexit
    atexit.register(at_exit)

    args = parse_args()
    sock = socket_config(socket_port=args.input_port)

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

    args.video = args.video.format(timestamp=str(time.time()), name=args.name)

    # for i in range(config.RESET_WAIT_SECS, 0, -1):
    #     print('Waiting for MultiWii board to reload... %02d' % i, end='\r')
    #     sys.stdout.flush()
    #     time.sleep(1)
    # print('-' * 79)

    frame = 0
    wait_time = config.CMD_WAIT_TIME
    nErrs = 0
    header_written = False
    started = time.time()
    cam_proc = None

    if config.RECORD_CAMERA:
        cam_proc = subprocess.Popen([
            '/root/magpi/record_camera.sh', args.video
        ])

    try:
        sock.recv(recv_buffer, socket.MSG_DONTWAIT)
    except socket.error:
        pass

    while True:
        if args.interactive:
            prompt = input('> ')
        timestamp = time.time()
        if nErrs > 1:
            if timestamp <= (started + config.WARMUP_TIME):
                wait_time += 0.01
            nErrs = 0
        if args.interactive and prompt is not '':
            try:
                if prompt.lower() in ['exit', 'quit']:
                    raise SystemExit
                send_multiple_packets(sock, prompt.strip().split(','),
                                      wait_time)
            except KeyError:
                print('Invalid command')
            except struct.error as e:
                print('Invalid arguments to command (not enough?)')
                print(e)
        try:
            frame += 1
            data = get_multiple_packets(sock, args.log.split(','), wait_time)
            # data = {}
            # for arg in args.log.split(','):
            #     data[arg] = get_packet(sock, arg)
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
        except IndexError as e:
            nErrs += 1
            print(timestamp, e)
        except struct.error as e:
            nErrs += 1
            print(timestamp, e)
        if args.interactive:
            print('-' * 79)
        try:
            sock.recv(recv_buffer, socket.MSG_DONTWAIT)
        except socket.error:
            pass
        time.sleep(wait_time)

    if cam_proc is not None:
        cam_proc.terminate()


if __name__ == '__main__':
    main()
