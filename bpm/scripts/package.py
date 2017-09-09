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
import json
import sys

import arrow
import yaml

import bpm.database
from bpm.database import Subreddit
import bpm.json
import bpm.package

def lookup_sr(s, name):
    sr = s.query(Subreddit).get(name)
    if sr is None:
        print("Error: could not find /r/%s" % (subreddit_name))
        sys.exit(1)
    return sr

def main(argv0, argv):
    parser = argparse.ArgumentParser(prog=argv0, description="Generate package file")
    parser.add_argument("package_yml", metavar="package.yml", help="Package configuration file")
    parser.add_argument("--version", "-v", type=int, help="Package version number")
    parser.add_argument("-f", action="store_true", help="Format output")
    bpm.database.add_database_arguments(parser)
    args = parser.parse_args(argv)

    engine = bpm.database.init_from_args(args)
    s = bpm.database.Session()

    with open(args.package_yml) as file:
        package_config = yaml.safe_load(file)

    # Look up all filter subreddits (regardless of whether or not they're
    # being packaged).
    filters = {}
    for name in package_config.get("Filtering", []):
        sr = lookup_sr(s, name)
        ss = sr.latest_update.stylesheet
        filters[name] = {emote.name for emote in ss.emotes}

    subreddit_data = {} # name -> data
    for name in package_config["Subreddits"]:
        sr = lookup_sr(s, name)
        subreddit_data[name] = bpm.package.pkg_subreddit(package_config, filters, sr)

    metadata = bpm.package.pkg_metadata(package_config, args.version)
    emotes = bpm.package.pkg_emotes(package_config, subreddit_data)

    # Todo
    flags = None
    css = None
    svgs = None

    content = bpm.package.build_package(metadata, subreddit_data, emotes, flags, css, svgs)
    data = bpm.package.build_file("package", content)

    if args.f:
        text = bpm.json.dumps_config(data, 5)
    else:
        text = json.dumps(data, separators=(",", ":"))
    print(text)

if __name__ == "__main__":
    main(sys.argv[0], sys.argv[1:])
