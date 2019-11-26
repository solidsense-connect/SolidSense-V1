# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:
# Purpose:  Argument paser
#              Shall run on LInux only
#
# Author:      Nicolas Albarel
#
# Created:     15/07/2019
# Copyright:   (c) Laurent Carre - Sterwen Technology 2019
# Licence:
#-------------------------------------------------------------------------------


"""
    Arguments
    =========

    Contains helpers to parse application arguments
"""


import json
import logging
import argparse
import datetime
import time
import yaml
import ssl
import pkg_resources


class Settings(object):
    """Simple class to handle library settings"""

    def __init__(self, settings: dict):
        super(Settings, self).__init__()
        for k, v in settings.items():
            self.__dict__[k] = v

    def __str__(self):
        return json.dumps(self.__dict__)

    def items(self):
        return self.__dict__.items()

    @classmethod
    def from_args(cls, args, skip_undefined=True):
        settings = dict()

        try:
            if args.settings:
                with open(args.settings, 'r') as f:
                    settings = yaml.load(f)
        except:
            pass

        for key, value in args.__dict__.items():
            if value is not None or skip_undefined is False:
                if key in settings and settings[key] is None:
                    settings[key] = value
                if key not in settings:
                    settings[key] = value

        return cls(settings)

    def __str__(self):
        return str(self.__dict__)


class ParserHelper(object):
    """
    ParserHelper

    Handles the creation and decoding of arguments

    """

    def __init__(self, description='argument parser',
                 formatter_class=argparse.ArgumentDefaultsHelpFormatter):
        super(ParserHelper, self).__init__()
        self._parser = argparse.ArgumentParser(
            description=description,
            formatter_class=formatter_class)

        self._groups = dict()

    @property
    def parser(self):
        """ Returns the parser object """
        return self._parser

    @property
    def arguments(self):
        """ Returns arguments that it can parse and throwing an error otherwise """
        self._arguments = self.parser.parse_args()
        return self._arguments

    @property
    def known_arguments(self):
        """ returns the unknown arguments it could not parse """
        self._arguments, self._unknown_arguments = self.parser.parse_known_args()
        return self._arguments

    @property
    def unkown_arguments(self):
        """ returns the unknown arguments it could not parse """
        return self._unknown_arguments

    def settings(self, settings_class=None, skip_undefined=True)->'Settings':
        self._arguments = self.parser.parse_args()

        if settings_class is None:
            settings_class = Settings

        settings = settings_class.from_args(self._arguments, skip_undefined)

        return settings

    def __getattr__(self, name):
        if name not in self._groups:
            self._groups[name] = self._parser.add_argument_group(name)

        return self._groups[name]

    def add_file_settings(self):
        """ For file setting handling"""
        self.file_settings.add_argument('--settings',
                                        type=str,
                                        required=False,
                                        default='settings.yml',
                                        help='settings file')

    def add_transport(self):
        """ Transport module arguments """
        self.transport.add_argument('-s', '--host',
                                    default="127.0.0.1",
                                    type=str,
                                    help="gRPC server address")

        self.transport.add_argument('-p',
                                    '--port',
                                    default=9883,
                                    type=int,
                                    help="gRPC server port")

        self.transport.add_argument('-fp',
                                    '--full_python',
                                    default=False,
                                    action='store_true',
                                    help="Do not use C extension for optimization")

        self.transport.add_argument('-iepf',
                                    '--ignored_endpoints_filter',
                                    default="[240-255]",
                                    help="Destination endpoints list to ignore (not published)")



    def dump(self, path):
        """ dumps the arguments into a file """
        with open(path, 'w') as f:
            f.write(serialize(vars(self._arguments)))
