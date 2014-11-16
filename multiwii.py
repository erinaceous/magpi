# vim: set tabstop=4 shiftwidth=4 textwidth=79 cc=72,79:
"""
    multiwii: Definitions of MultiWii serial protocol commands.
    Uses http://www.multiwii.com/wiki/index.php?title=Multiwii_Serial_Protocol
    for reference
    Original Author: Owain Jones [github.com/erinaceous] [contact@odj.me]
"""
# TODO: Find out why TX commands aren't working!!!
# TODO: Docstrings!
# TODO: Maybe rename some functions so their names are more sensical

from __future__ import print_function
from collections import OrderedDict
import struct


ENDIANNESS = '<'  # little endian. I assume that's what Atmel AVR chips are.
                  # (this is sent to the struct.pack and .unpack functions)


TX_TYPES = {  # mapping between weird struct format types and human readable
    'char': 'c',
    'uint8': 'B',
    'uint16': 'H',
    'uint32': 'L',
    'int8': 'b',
    'int16': 'h',
    'int32': 'l',
    'str': 's'
}


class Command:
    CMD_HEADER = '$M<'
    RCV_HEADER = '$M>'

    class ChecksumError(Exception):
        pass

    class NotACommand(Exception):
        pass

    def __init__(self, mid, tx, ignoreChecksum, *params):
        self.tx = False
        self.ignoreChecksum = False
        if tx in [1, True, 'tx']:
            self.tx = True
        if ignoreChecksum in [1, True, 'yes', 'ignore']:
            self.ignoreChecksum = True
        self.parameters = OrderedDict()
        for i, char in enumerate(Command.RCV_HEADER):
            self.parameters['_m%d' % i] = 'char'
        self.parameters['_len'] = 'uint8'
        self.parameters['_id'] = 'uint8'
        self.message_id = mid
        for (name, dtype) in params:
            self.parameters[name] = dtype
        self.parameters['_checksum'] = 'uint8'
        self.dtype = ENDIANNESS + ''.join([
            TX_TYPES[value] for value in self.parameters.values()    
        ])
        self.dtype_cmd = ENDIANNESS + ''.join([
            TX_TYPES[value] for key, value in self.parameters.items()
            if key.startswith('_')
        ])

    def parse(self, message):
        if message.startswith(Command.RCV_HEADER) is False:
            raise Command.NotACommand(
                "Message received didn't begin with $M>. Message:\n" +
                str(message))
        checksum = 0
        for byte in message[3:-1]:
            checksum ^= (ord(byte) & 0xFF)
        data = struct.unpack(self.dtype, message)
        output = OrderedDict()
        for i, key in enumerate(self.parameters.keys()):
            output[key] = data[i]
        if checksum != output['_checksum'] and not self.ignoreChecksum:
            raise Command.ChecksumError(
                "Checksum is %d, should be %d.\n" % (
                    output['_checksum'], checksum)
                + "Output: " + str(output))
        return output

    def get_command(self, *payload):
        pl_len = len(payload)
        args = [x for x in Command.CMD_HEADER]
        args.extend([pl_len, self.message_id])
        args.extend(payload)
        # args.append(checksum)
        checksum = 0
        if self.tx:
            message = struct.pack(self.dtype[:-1], *args)
        else:
            message = struct.pack(self.dtype_cmd[:-1], *args)
        for byte in message[3:]:
            checksum ^= (ord(byte) & 0xFF)
        message += struct.pack('<B', checksum)
        return message

    def get_response_length(self):
        return struct.calcsize(self.dtype)

    def get_command_length(self):
        return struct.calcsize(self.dtype_cmd)


COMMANDS = {
    # RX COMMANDS

    'MSP_IDENT': Command(100, 'rx', 'no',
                         ('VERSION', 'uint8'),
                         ('MULTITYPE', 'uint8'),
                         ('MSP_VERSION', 'uint8'),
                         ('capability', 'uint32')
    ),
    'MSP_STATUS': Command(101, 'rx', 'no',
                          ('cycleTime', 'uint16'),
                          ('i2c_errors_count', 'uint16'),
                          ('sensor', 'uint16'),
                          ('flag', 'uint32'),
                          ('global_conf.currentSet', 'uint8')
    ),
    'MSP_RAW_IMU': Command(102, 'rx', 'no',
                           ('accx', 'int16'),
                           ('accy', 'int16'),
                           ('accz', 'int16'),
                           ('gyrx', 'int16'),
                           ('gyry', 'int16'),
                           ('gyrz', 'int16'),
                           ('magx', 'int16'),
                           ('magy', 'int16'),
                           ('magz', 'int16')
    ),
    'MSP_SERVO': Command(103, 'rx', 'no',
                         *[('Servo%d' % i, 'uint16') for i in range(1, 9)]
    ),
    'MSP_MOTOR': Command(104, 'rx', 'no',
                         *[('Motor%d' % i, 'uint16') for i in range(1, 9)]
    ),
    'MSP_RC': Command(105, 'rx', 'no', *list(zip(
        ['ROLL', 'PITCH', 'YAW', 'THROTTLE', 'AUX1', 'AUX2', 'AUX3', 'AUX4'],
        ['uint16'] * 8
    ))),
    'MSP_RAW_GPS': Command(106, 'rx', 'no',
                           ('GPS_FIX', 'uint8'),
                           ('GPS_numSat', 'uint8'),
                           ('GPS_coord[LAT]', 'uint32'),
                           ('GPS_coord[LON]', 'uint32'),
                           ('GPS_altitude', 'uint16'),
                           ('GPS_speed', 'uint16'),
                           ('GPS_ground_course', 'uint16')
    ),
    'MSP_COMP_GPS': Command(107, 'rx', 'no',
                            ('GPS_distanceToHome', 'uint16'),
                            ('GPS_directionToHome', 'uint16'),
                            ('GPS_update', 'uint8')
    ),
    'MSP_ATTITUDE': Command(108, 'rx', 'no',
                            ('angx', 'int16'),
                            ('angy', 'int16'),
                            ('heading', 'int16')
    ),
    'MSP_ALTITUDE': Command(109, 'rx', 'no',
                            ('EstAlt', 'int32'),
                            ('vario', 'int16')
    ),
    'MSP_ANALOG': Command(110, 'rx', 'no',
                          ('vbat', 'uint8'),
                          ('intPowerMeterSum', 'uint16'),
                          ('rssi', 'uint16'),
                          ('amperage', 'uint16')
    ),
    'MSP_RC_TUNING': Command(111, 'rx', 'no',
                             ('byteRC_RATE', 'uint8'),
                             ('byteRC_EXPO', 'uint8'),
                             ('byteRollPitchRate', 'uint8'),
                             ('byteYawRate', 'uint8'),
                             ('byteDynThrPID', 'uint8'),
                             ('byteThrottle_MID', 'uint8'),
                             ('byteThrottle_EXPO', 'uint8')
    ),
    # Fix also
    'MSP_PID': Command(112, 'rx', 'yes',
                       *sum([
                            list(zip(['%s_%s' % (item, c) for c in 'PID'],
                                     ['uint8'] * 3))
                            for item in ['ROLL', 'PITCH', 'YAW', 'ALT', 'POSR',
                                         'NAVR', 'LEVEL', 'MAG', 'VEL']
                       ], [])
    ),
    # MSP_BOX / 113 is special command which needs some custom code
    'MSP_MISC': Command(114, 'rx', 'no',
                        ('intPowerTrigger1', 'uint16'),
                        ('conf.minthrottle', 'uint16'),
                        ('MAXTHROTTLE', 'uint16'),
                        ('MINCOMMAND', 'uint16'),
                        ('conf.failsafe_throttle', 'uint16'),
                        ('plog.arm', 'uint16'),
                        ('plog.lifetime', 'uint32'),
                        ('conf.mag_declination', 'uint16'),
                        ('conf.vbatscale', 'uint8'),
                        ('conf.vbatlevel_warn1', 'uint8'),
                        ('conf.vbatlevel_warn2', 'uint8'),
                        ('conf.vbatlevel_crit', 'uint8')
    ),
    'MSP_MOTOR_PINS': Command(115, 'rx', 'no',
                              *[('MotorPin%d' % i, 'uint8')
                                for i in range (1, 9)]
    ),
    # 'MSP_BOXNAMES': Command(116, ('MSP_BOXNAMES', 'str')),
    # 'MSP_PIDNAMES': Command(117, ('MSP_PIDNAMES', 'str')),
    'MSP_WP': Command(118, 'rx', 'no',
                      ('wp_no', 'uint8'),
                      ('lat', 'uint32'),
                      ('lon', 'uint32'),
                      ('AltHold', 'uint32'),
                      ('heading', 'uint16'),
                      ('time_to_stay', 'uint16'),
                      ('nav_flag', 'uint8')
    ),
    # too lazy to implement MSP_BOXIDS / 119
    # TODO: implement MSP_SERVO_CONF / 120

    # TX COMMANDS

    'MSP_SET_MOTOR': Command(214, 'tx', 'no',
                             *[('Motor%d' % i, 'uint16')
                               for i in range(1, 9)]
    ),
    'MSP_SET_RAW_RC': Command(200, 'tx', 'no', *list(zip(
        ['ROLL', 'PITCH', 'YAW', 'THROTTLE', 'AUX1', 'AUX2', 'AUX3', 'AUX4'],
        ['uint16'] * 8
    ))),
    'MSP_SET_RAW_GPS': Command(201, 'tx', 'no',
                               ('GPS_FIX', 'uint8'),
                               ('GPS_numSat', 'uint8'),
                               ('GPS_coord[LAT]', 'uint32'),
                               ('GPS_coord[LON]', 'uint32'),
                               ('GPS_altitude', 'uint16'),
                               ('GPS_speed', 'uint16')
    ),
    'MSP_SET_RC_TUNING': Command(204, 'tx', 'no',
                                 ('byteRC_RATE', 'uint8'),
                                 ('byteRC_EXPO', 'uint8'),
                                 ('byteRollPitchRate', 'uint8'),
                                 ('byteYawRate', 'uint8'),
                                 ('byteDynThrPID', 'uint8'),
                                 ('byteThrottle_MID', 'uint8'),
                                 ('byteThrottle_EXPO', 'uint8')
    ),
    # FIXME PID controller rx/tx definitions
    # 'MSP_SET_PID': Command(202,
    #
    # ),
    'MSP_SET_PID': Command(202, 'tx', 'no',
                           *sum([
                                 list(zip(['%s_%s' % (item, c) for c in 'PID'],
                                          ['uint8'] * 3))
                                 for item in ['ROLL', 'PITCH', 'YAW', 'ALT',
                                              'POSR', 'NAVR', 'LEVEL', 'MAG',
                                              'VEL']
                                ], [])
    ),
    # FIXME MSP_[SET_]BOX
    # 'MSP_SET_BOX': Command(203,
    #
    # ),
    'MSP_SET_MISC': Command(207, 'tx', 'no',
                            ('intPowerTrigger1', 'uint16'),
                            ('conf.minThrottle', 'uint16'),
                            ('MAXTHROTTLE', 'uint16'),
                            ('MINCOMMAND', 'uint16'),
                            ('conf.failsafe_throttle', 'uint16'),
                            ('plog.arm', 'uint16'),
                            ('plog.lifetime', 'uint32'),
                            ('conf.mag_declination', 'uint16'),
                            ('conf.vbatscale', 'uint8'),
                            ('conf.vbatlevel_warn1', 'uint8'),
                            ('conf.vbatlevel_warn2', 'uint8'),
                            ('conf.vbatlevel.crit', 'uint8')
    ),
    'MSP_SET_WP': Command(209, 'tx', 'no',
                          ('wp_no', 'uint8'),
                          ('lat', 'uint32'),
                          ('lon', 'uint32'),
                          ('AltHold', 'uint32'),
                          ('heading', 'uint16'),
                          ('time_to_stay', 'uint16'),
                          ('nav_flag', 'uint8')
    ),
    # TODO MSP_SET_SERVO_CONF
    'MSP_ACC_CALIBRATION': Command(205, 'tx', 'no'),
    'MSP_MAG_CALIBRATION': Command(206, 'tx', 'no'),
    'MSP_RESET_CONF': Command(208, 'tx', 'no'),
    'MSP_SELECT_SETTING': Command(210, 'tx', 'no',
                                  ('global_conf.currentSet', 'uint8')),
    'MSP_SET_HEAD': Command(211, 'tx', 'no', ('magHold', 'int16')),
    'MSP_BIND': Command(240, 'tx', 'no'),
    'MSP_EEPROM_WRITE': Command(250, 'tx', 'no')
}


def tx_generate(name, *payload):
    return COMMANDS[name].get_command(*payload)


def rx_parse(name, message):
    return COMMANDS[name].parse(message)


def get_command(name):
    return COMMANDS[name].get_command()


def get_command_length(name):
    return COMMANDS[name].get_command_length()


def get_response_length(name):
    return COMMANDS[name].get_response_length()


def get_command_dtype(name):
    return COMMANDS[name].dtype_cmd


def get_response_dtype(name):
    return COMMANDS[name].dtype
