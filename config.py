# vim: set tabstop=4 shiftwidth=4 textwidth=79 cc=72,79:
"""
    config: All the config variables for brains.
    Original Author: Owain Jones [github.com/erinaceous] [contact@odj.me]
"""

from __future__ import print_function


NAME = 'magpi'
SERIAL_PORT = '/dev/multiwii'
OUTPUT_SOCKET = '/tmp/multiwii.sock'
OUTPUT_PORT = 5001
# UDP_PORT = 43110  # UDP port on which to broadcast telemetry. -1 to disable.
UDP_PORT = -1
HEADER_EVERY = 10
FILE_PREFIX = '/data/flight_{timestamp}'      # File in which to save
                                              # telemetry. None to disable.
# VIDEO_FILE = '/data/flight_{timestamp}.h264'
RESET_WAIT_SECS = 3  # when we first access MW board, it resets. Wait this long
CMD_WAIT_TIME = 0.01  # minimum time between serial commands.
ITER_TIME = 0.8
WARMUP_TIME = 10

THINGS_TO_LOG = 'MSP_ALTITUDE,MSP_RAW_IMU,MSP_RAW_GPS,MSP_ATTITUDE,MSP_RC,'
THINGS_TO_LOG += 'MSP_MOTOR'

RECORD_CAMERA = True
