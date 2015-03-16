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

import argparse
import sys

import bpm.database
import bpm.scripts

def main(argv0, argv):
    parser = argparse.ArgumentParser(prog=argv0, description="Initialize database tables")
    bpm.database.add_database_arguments(parser)
    bpm.scripts.add_config_arguments(parser)

    args = parser.parse_args(argv)
    config = bpm.scripts.load_config(argv0, args)
    engine = bpm.database.init_from_config(config, args)

    bpm.database.init_tables(engine)

if __name__ == "__main__":
    main(sys.argv[0], sys.argv[1:])
