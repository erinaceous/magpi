#!/usr/bin/env python
# vim: set tabstop=4 shiftwidth=4 textwidth=79 cc=72,79:
"""
    setup: 
    Original Author: Owain Jones [github.com/erinaceous] [contact@odj.me]
"""

from __future__ import print_function
from distutils.core import setup

setup(
    name='multiwii',
    version='0.1',
    description='Python library and tools for communicating with flight ' +\
                'controllers running the MultiWii serial protocol',
    author='Owain Jones',
    author_email='contact@odj.me',
    url='http://github.com/erinaceous/magpi',
    packages=['multiwii'],
    package_dir={'multiwii': 'src'},
)
