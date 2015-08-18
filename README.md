magpi
=====

Code for my Quadcopter, which is using a Raspberry Pi as its brains.
Includes a Python library for speaking the MultiWii Serial Protocol / MSP.

installing & using the multiwii library
=======================================

this is handled by distutils, so simply:

    sudo python setup.py install

then you can import the library into your python scripts.

this library is only responsible for generating the MultiWii serial commands --
it doesn't do any actual communication by itself. `bin/multiwiid.py` does do
this -- it takes exclusive control of a serial device and listens on the
network, by default on UDP port 5001.

If you can successfully run `multiwiid`, from your own code you just need to
create a client socket and connect to it. By default you'll need to copy
`config.ini` to `/etc/magpi.ini` on the computer connected to your flight
controller.

See `tools/test_arm.py` and `tools/test_controller.py` for two examples of this;
sending RC commands to the flight controller through the multiwiid server.

Otherwise, you can just use [http://pyserial.sourceforge.net/](PySerial) to send
commands to your flight controller and read their responses.

using the other stuff
=====================

the other stuff in this repo is the scaffolding for getting an Arch-Pi linux
system up and running, with wireless networking and multiwiid starting by
default, plus some remote tools e.g. in `tools/` for connecting the MultiWiiConf
GUI to a flight controller over the network.

caveats
=======

I massively reorganized this without testing it, and currently unable to push
the latest changes from my quadcopter, so some of the external gubbins may not
work! the multiwii library does, however, import successfully.
