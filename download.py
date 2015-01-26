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

import bpm.json
import bpm.reddit

def main(argv0, argv):
    parser = argparse.ArgumentParser(prog=argv0, description="Download stylesheet")
    #bpm.scripts.add_config_arguments(parser)
    parser.add_argument("--raw", action="store_true", help="Output raw API response")
    parser.add_argument("-o", help="Output file (css or raw)")
    parser.add_argument("-i", help="Output file (images)")
    parser.add_argument("subreddit", help="Subreddit")

    args = parser.parse_args(argv)
    #config = bpm.scripts.load_config(argv0, args)

    if args.raw:
        filename = args.o or args.subreddit + ".json"
        data = bpm.reddit.download_raw_stylesheet(args.subreddit)
        with open(filename, "w") as file:
            bpm.json.dump_config(data, file, max_depth=3)
    else:
        css_filename = args.o or args.subreddit + ".css"
        images_filename = args.i or args.subreddit + "-images.json"
        css, images = bpm.reddit.download_stylesheet(args.subreddit)
        with open(css_filename, "w") as file:
            file.write(css)
        with open(images_filename, "w") as file:
            bpm.json.dump_config(images, file)

if __name__ == "__main__":
    main(sys.argv[0], sys.argv[1:])
