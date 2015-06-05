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

import arrow

import bpm.database

def main(argv0, argv):
    parser = argparse.ArgumentParser(prog=argv0, description="Add subreddit")
    bpm.database.add_database_arguments(parser)
    parser.add_argument("subreddit", help="Subreddit")

    args = parser.parse_args(argv)
    engine = bpm.database.init_from_args(args)

    now = arrow.utcnow()

    s = bpm.database.Session()
    sr = bpm.database.Subreddit(subreddit_name=args.subreddit, added=now)
    s.add(sr)
    s.commit()

if __name__ == "__main__":
    main(sys.argv[0], sys.argv[1:])
