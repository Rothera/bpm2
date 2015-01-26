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

import datetime
import html.parser
import time
import urllib

import logbook

import requests

log = logbook.Logger(__name__)

USER_AGENT = "BetterPonymotes Backend Services (/u/Typhos)"
REDDIT = "https://www.reddit.com"

REQUEST_DELAY = datetime.timedelta(seconds=2)

_last_request = None

def check_request_timer():
    if _last_request is not None:
        now = datetime.datetime.utcnow()
        dt = now - _last_request
        if dt < REQUEST_DELAY:
            time.sleep((REQUEST_DELAY - dt).seconds)

def reset_request_timer():
    global _last_request
    _last_request = datetime.datetime.utcnow()

def download(url):
    check_request_timer()
    try:
        log.debug("Downloading {}", url)
        r = requests.get(url, headers={"User-Agent": USER_AGENT})
    finally:
        reset_request_timer()
    return r

def check_search_redirect(r):
    # Check for redirects
    url = urllib.parse.urlparse(r.url)
    if url.path.startswith("/subreddits/search"):
        raise ValueError("Subreddit redirected to search (invalid name?)")

def download_raw_stylesheet(subreddit):
    url = "%s/r/%s/about/stylesheet.json" % (REDDIT, subreddit)
    r = download(url)
    r.raise_for_status()
    check_search_redirect(r)
    data = r.json()
    assert data["kind"] == "stylesheet"
    return data

def download_stylesheet(subreddit):
    data = download_raw_stylesheet(subreddit)

    css = data["data"]["stylesheet"]

    # FIXME: reddit does something weird and encodes this as if it were HTML.
    # So selectors like "foo > bar" will get munged into "foo &gt; bar". Since
    # I can't find any way around this we'll just fix it ourselves.
    css = html.parser.unescape(css)

    # Reformat images list. We don't need the "link": "url(%%image%%)" part.
    images = {img["name"]: img["url"] for img in data["data"]["images"]}

    return (css, images)
