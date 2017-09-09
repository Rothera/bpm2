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

import arrow

import bpm.images

FILE_MAGIC = "rainbow dash is best pony"
FILE_SCHEMA_VERSION = 1

def build_file(filetype, content):
    data = {
        "__betterponymotes_magic": FILE_MAGIC,
        "__betterponymotes_schema": FILE_SCHEMA_VERSION,
        "__betterponymotes_filetype": filetype,
        "__betterponymotes_content": content
    }
    return data

PACKAGE_SCHEMA_VERSION = 1

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

def pkg_subreddit(package_config, filters, sr):
    # Create set of all filtered emote names (except our own)
    applied_filters = set()
    for (name, f) in filters.items():
        if name != sr.subreddit_name:
            applied_filters.update(f)

    ss = sr.latest_update.stylesheet

    emotes = {}
    images = {}

    for emote in ss.emotes:
        # Ignore filtered emotes
        if emote.name in applied_filters:
            continue

        # Serialize emote
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

def pkg_emotes(package_config, subreddit_data):
    pass
