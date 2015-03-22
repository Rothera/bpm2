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

import re

_redditmedia_regexp = re.compile(r"^http://([a-z])\.thumbs\.redditmedia\.com/([a-zA-Z0-9_-]+)\.(png|jpg)$")
_nohttp_regexp      = re.compile(     r"^//([a-z])\.thumbs\.redditmedia\.com/([a-zA-Z0-9_-]+)\.(png|jpg)$")

def image_filename(url):
    m = _redditmedia_regexp.match(url)
    if m:
        bucket, filename, ext = m.groups()
        return "redditmedia-%s-%s.%s" % (bucket, filename, ext)

    m = _nohttp_regexp.match(url)
    if m:
        bucket, filename, ext = m.groups()
        return "redditmedia-%s-%s.%s" % (bucket, filename, ext)

    raise Exception("Unknown image URL", url)

def image_download_url(url):
    m = _redditmedia_regexp.match(url)
    if m:
        bucket, filename, ext = m.groups()
        bucket += ".thumbs.redditmedia.com"
        return "https://s3.amazonaws.com/%s/%s.%s" % (bucket, filename, ext)

    m = _nohttp_regexp.match(url)
    if m:
        bucket, filename, ext = m.groups()
        bucket += ".thumbs.redditmedia.com"
        return "https://s3.amazonaws.com/%s/%s.%s" % (bucket, filename, ext)

    # Can't rewrite, but can still download
    print("Warning: Don't know how to rewrite URL:", url)
    return url
