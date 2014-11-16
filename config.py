# vim: set tabstop=4 shiftwidth=4 textwidth=79 cc=72,79:
"""
    config: All the config variables for brains.
    Original Author: Owain Jones [github.com/erinaceous] [contact@odj.me]
"""

from __future__ import print_function


SERIAL_PORT = '/dev/ttyUSB0'
UDP_PORT = 43110  # UDP port on which to broadcast telemetry. -1 to disable.
DATA_FILE = 'data/flight_{timestamp}.csv.gz'  # File in which to save
                                              # telemetry. None to disable.
RESET_WAIT_SECS = 9  # when we first access MW board, it resets. Wait this long
CMD_WAIT_TIME = 0.01  # minimum time between serial commands.
ITER_TIME = 0.8

THINGS_TO_LOG = 'MSP_ALTITUDE,MSP_RAW_IMU,MSP_RAW_GPS,MSP_ATTITUDE,MSP_RC,'
THINGS_TO_LOG += 'MSP_MOTOR'
