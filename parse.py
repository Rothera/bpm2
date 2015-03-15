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

import bpm.css
import bpm.json

def main(argv0, argv):
    parser = argparse.ArgumentParser(prog=argv0, description="Parse stylesheet")
    parser.add_argument("-j", action="store_true", help="JSON output")
    parser.add_argument("stylesheet", help="Stylesheet")

    args = parser.parse_args(argv)

    with open(args.stylesheet) as file:
        css = file.read()

    rules = bpm.css.parse_stylesheet(css)

    if args.j:
        data = [rule.serialize() for rule in rules]
        json = bpm.json.dumps_config(data, max_depth=3)
        print(json)
    else:
        for rule in rules:
            print(rule)

if __name__ == "__main__":
    main(sys.argv[0], sys.argv[1:])
