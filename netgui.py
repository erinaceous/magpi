#!/usr/bin/env python2
# vim: set tabstop=4 shiftwidth=4 textwidth=79 cc=72,79:
"""
    netgui: Listens for UDP broadcasts. Uses PyGame to visualise
    telemetry data.
    Original Author: Owain Jones [github.com/erinaceous] [contact@odj.me]
"""

from __future__ import print_function
import collections
import argparse
import strconv
import config
import pygame
import select
import socket
import time


so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
so.bind(('<broadcast>', config.UDP_PORT))
so.setblocking(0)


class args:
    name = 'magpi'

buffersize = 1024
screen = pygame.display.set_mode((800, 600))


def mapRange(x, from_min, from_max, to_min, to_max):
    return (x - from_min) * (to_max - to_min) / (from_max - from_min) + to_min


class Joystick:
    def __init__(self, minimum=1000, center=1500,
                 maximum=2000, width=128,
                 height=128, data=(1500, 1500), stick=(64, 64), pos=(0, 0)):
        self.minimum = minimum
        self.maximum = maximum
        self.center = center
        self.width = width
        self.height = height
        self.halfwidth = width / 2
        self.halfheight = height / 2
        self.data = data
        self.stick = stick
        self.bgcolor = 0x0000FF
        self.fgcolor = 0x00FFFF
        self.pos = pos

    def update(self, data):
        self.data = data
        self.stick = (
            mapRange(data[0], self.minimum, self.maximum, 0, self.width),
            mapRange(data[1], self.minimum, self.maximum, 0, self.height)
        )

    def draw(self, surface):
        pygame.draw.rect(surface, self.bgcolor,
                         (self.pos[0], self.pos[1], self.width, self.height),
                         2)
        pygame.draw.line(surface, 0x000000,
                         (self.pos[0] + self.halfwidth, self.pos[1]),
                         (self.pos[0] + self.halfwidth,
                          self.pos[1] + self.height), 1)
        pygame.draw.circle(surface, self.bgcolor,
                           (self.pos[0] + self.halfwidth,
                            self.pos[1] + self.halfheight),
                           self.halfwidth)
        pygame.draw.circle(surface, self.fgcolor,
                           (self.pos[0] + self.stick[0],
                            (self.pos[1] + self.height) - self.stick[1]),
                           10)


dials = {
    'left': Joystick(pos=(10, 10)),
    'right': Joystick(pos=(158, 10))
}
c = pygame.time.Clock()
header = None
data = None
output = collections.OrderedDict()

while True:
    result = select.select([so], [], [])
    msg = ''
    while '\n' not in msg:
        msg += result[0][0].recv(buffersize)
    # print(msg)
    if msg.startswith('$MAGPI[%s]_H' % args.name):
        header = msg.strip().split(',')
    elif msg.startswith('$MAGPI[%s]_D' % args.name):
        data = [strconv.convert(d) for d in msg.strip().split(',')]
    if header is not None and data is not None:
        for i, key in enumerate(header):
            output[key] = data[i]

    screen.fill(0x000000)
    for event in pygame.event.get():
        pass

    try:
        dials['left'].update((output['RC_YAW'], output['RC_PITCH']))
        dials['right'].update((output['RC_ROLL'], output['RC_THROTTLE']))
    except KeyError:
        pass

    for dial_name, dial in dials.items():
        dial.draw(screen)

    pygame.display.update()
    c.tick(60)
