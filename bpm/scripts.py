#!/usr/bin/env python3
################################################################################
##
## This file is part of BetterPonymotes.
## Copyright (c) 2015 Typhos.
##
## This program is free software: you can redistribute it and/or modify it
## under the terms of the GNU Affero General Public License as published by
## the Free Software Foundation, either version 3 of the License, or (at your
## option) any later version.
##
## This program is distributed in the hope that it will be useful, but WITHOUT
## ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
## FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
## for more details.
##
## You should have received a copy of the GNU Affero General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
################################################################################

import os.path

import bpm.json

DEFAULT_CONFIG_FILE = "config.json"

def add_config_arguments(parser):
    parser.add_argument("--config", help="Alternate configuration file")
    parser.add_argument("--database", help="Alternate database URI")
    parser.add_argument("--database-debug", action="store_true", help="Enable SQLAlchemy debugging")

def load_config(argv0, args):
    if args.config:
        filename = args.config
    else:
        filename = os.path.join(os.path.dirname(argv0), DEFAULT_CONFIG_FILE)

    try:
        with open(filename) as file:
            config = bpm.json.load(file)
    except IOError:
        config = {}

    return config