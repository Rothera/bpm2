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
import os.path
import sys

import arrow
import requests

import bpm.database
import bpm.images
from bpm.database import Subreddit, Stylesheet, Image

def mark_download(s, image):
    image.downloaded = arrow.utcnow()
    s.add(image)
    s.commit()

def main(argv0, argv):
    parser = argparse.ArgumentParser(prog=argv0, description="Download pending images")
    bpm.database.add_database_arguments(parser)
    parser.add_argument("-n", action="store_true", help="Don't commit")
    parser.add_argument("--fix", action="store_true", help="Mark existing files as downloaded")
    parser.add_argument("-l", action="store_true", help="List pending images")
    args = parser.parse_args(argv)

    engine = bpm.database.init_from_args(args)
    s = bpm.database.Session()

    if args.l:
        rows = s.query(Image, Subreddit, Stylesheet).join(Stylesheet).filter(Image.downloaded == None).order_by(Subreddit.subreddit_name, Image.url).all()
        for (image, sr, ss) in rows:
            print("%s  %-25s %s" % (ss.downloaded.format("YYYY-MM-DD"), sr.subreddit_name, image.url))
        return

    images = s.query(Image).filter_by(downloaded=None).order_by(Image.image_id).all()

    for image in images:
        path = os.path.join("images", image.filename)

        if os.path.exists(path):
            print("Notice: %s already exists. Marking as downloaded." % (image.filename))
            mark_download(s, image)
            continue

        if args.fix:
            continue

        real_url = bpm.images.image_download_url(image.url)
        print("Downloading", real_url, "->", path)

        r = requests.get(real_url)
        r.raise_for_status()

        with open(path, "wb") as file:
            file.write(r.content)

        if not args.n:
            mark_download(s, image)

if __name__ == "__main__":
    main(sys.argv[0], sys.argv[1:])
