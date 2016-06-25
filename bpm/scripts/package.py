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
import bpm.images
import bpm.json
import bpm.package

PACKAGE_SCHEMA_VERSION = 1

def pkg_subreddit(sr, ss):
    emotes = {}
    images = {}

    for emote in ss.emotes:
        emote_data = []
        for part in emote.parts:
            emote_data.append(part.serialize())
            if part.sprite_image_url:
                images[part.sprite_image_url] = None
        emotes[emote.name] = emote_data

    for image in ss.images:
        pname = "%%" + image.name + "%%"
        if pname in images:
            # Map images to proper download URL's. This rewrites to HTTPS and
            # also evades Cloudflare, just in case.
            images[pname] = bpm.images.image_download_url(image.url)

    data = {"emotes": emotes, "images": images}
    return data

def pkg_metadata(package_config, package_version):
    m = package_config["Metadata"]
    timestamp = arrow.utcnow().format("YYYY-MM-DD HH:mm:ss")
    data = {
        "name": m["Name"],
        "version": package_version,
        "timestamp": timestamp,
        "description": m["Description"],
        "repository": m["Repository"]
    }
    return data

def build_package(metadata, subreddit_data, emotes, flags, css, svgs):
    data = {
        "schema": PACKAGE_SCHEMA_VERSION,
        "metadata": metadata,
        "content": subreddit_data,
        "emotes": emotes,
        "flags": flags,
        "css": css,
        "svgs": svgs
    }
    return data

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

    subreddit_data = {} # name -> data

    for subreddit_name in package_config["Subreddits"]:
        sr = s.query(Subreddit).get(subreddit_name)
        if sr is None:
            print("Error: could not find /r/%s" % (subreddit_name))
            sys.exit(1)

        ss = sr.latest_update.stylesheet
        subreddit_data[subreddit_name] = pkg_subreddit(sr, ss)

    metadata = pkg_metadata(package_config, args.version)

    emotes = {} # Todo

    # Todo
    flags = None
    css = None
    svgs = None

    content = build_package(metadata, subreddit_data, emotes, flags, css, svgs)
    data = bpm.package.build_file("package", content)

    if args.f:
        text = bpm.json.dumps_config(data, 5)
    else:
        text = json.dumps(data, separators=(",", ":"))
    print(text)

if __name__ == "__main__":
    main(sys.argv[0], sys.argv[1:])
