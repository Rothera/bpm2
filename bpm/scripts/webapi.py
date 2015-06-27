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
import bpm.webapi

def main(argv0, argv):
    parser = argparse.ArgumentParser(prog=argv0, description="Run data API")
    bpm.database.add_database_arguments(parser)
    parser.add_argument("--flask-debug", action="store_true", help="Enable Flask debugging")
    parser.add_argument("--host", help="Host to bind to")
    parser.add_argument("--port", type=int, help="Port to bind to")
    args = parser.parse_args(argv)

    engine = bpm.database.init_from_args(args)
    bpm.database.setup_flask(bpm.webapi.app)

    bpm.webapi.app.run(host=args.host, port=args.port, debug=args.flask_debug)

if __name__ == "__main__":
    main(sys.argv[0], sys.argv[1:])
