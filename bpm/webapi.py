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

import json

import flask

from bpm.database import Session
from bpm.database import Subreddit, Update, Stylesheet, Image, Emote, EmotePart

app = flask.Flask(__name__)

# Note: These functions do not omit redundant fields when used as child objects,
# e.g. we include the subreddit_name all the way down the subreddit -> update ->
# stylesheet object tree. This is in hopes that dumber clients will have an
# easier time parsing the output.

# Note: emote_id and part_id are pretty much useless, but maybe someone will
# find a purpose for them, so they remain in the output. They make a nice
# identifier.

def _serialize_subreddit(sr, detail_latest=False):
    data = {}
    data["subreddit_name"] = sr.subreddit_name
    data["added"] = sr.added.format()
    data["latest_update_id"] = sr.latest_update_id
    if sr.latest_update_id:
        data["latest_update"] = _serialize_update(sr.latest_update, detail=detail_latest)
    else:
        data["latest_update"] = None
    return data

def _serialize_update(update, detail=False):
    data = {}
    data["update_id"] = update.update_id
    data["subreddit_name"] = update.subreddit_name
    data["update_seq"] = update.update_seq
    data["stylesheet_id"] = update.stylesheet_id
    data["created"] = update.created.format()
    data["stylesheet"] = _serialize_stylesheet(update.stylesheet, detail=detail)
    return data

def _serialize_stylesheet(ss, detail=False):
    data = {}
    data["stylesheet_id"] = ss.stylesheet_id
    data["subreddit_name"] = ss.subreddit_name
    data["stylesheet_seq"] = ss.stylesheet_seq
    data["downloaded"] = ss.downloaded.format()
    data["css_hash"] = ss.css_hash
    if detail:
        data["images"] = {}
        for image in ss.images:
            data["images"][image.name] = _serialize_image(image)
        data["emotes"] = {}
        for emote in ss.emotes:
            data["emotes"][emote.name] = _serialize_emote(emote)
    return data

def _serialize_image(image):
    data = {}
    data["image_id"] = image.image_id
    data["stylesheet_id"] = image.stylesheet_id
    data["name"] = image.name
    data["url"] = image.url
    data["contains_emotes"] = image.contains_emotes
    return data

def _serialize_emote(emote):
    data = {}
    data["emote_id"] = emote.emote_id
    data["stylesheet_id"] = emote.stylesheet_id
    data["name"] = emote.name
    data["parts"] = []
    for part in emote.parts:
        part_data = part.serialize()
        part_data["part_id"] = part.part_id
        part_data["emote_id"] = part.emote_id
        data["parts"].append(part_data)
    return data

# Gets a subreddit listing
@app.route("/subreddits")
def subreddits():
    s = Session()
    subreddits = s.query(Subreddit).all()

    data = {}
    for sr in subreddits:
        data[sr.subreddit_name] = _serialize_subreddit(sr, detail_latest=False)

    return flask.jsonify(data)

# Gets subreddit details
@app.route("/r/<string:subreddit_name>")
def r_subreddit(subreddit_name):
    s = Session()
    sr = s.query(Subreddit).get(subreddit_name)
    data = _serialize_subreddit(sr, detail_latest=True)
    return flask.jsonify(data)

# Gets a subreddit recent update listing
@app.route("/r/<string:subreddit_name>/updates")
def r_subreddit_updates(subreddit_name):
    s = Session()
    updates = s.query(Update).filter_by(subreddit_name=subreddit_name).order_by(Update.update_seq.desc()).limit(10).all()
    data = {"updates": []}
    for update in updates:
        data["updates"].append(_serialize_update(update, detail=False))
    return flask.jsonify(data)

# Gets an update by ID
@app.route("/updates/<int:update_id>")
def update(update_id):
    s = Session()
    update = s.query(Update).get(update_id)
    data = _serialize_update(update, detail=True)
    return flask.jsonify(data)

# Gets an update by sequence number
@app.route("/r/<string:subreddit_name>/updates/<int:update_seq>")
def r_subreddit_update(subreddit_name, update_seq):
    s = Session()
    update = s.query(Update).filter_by(subreddit_name=subreddit_name, update_seq=update_seq).one()
    data = _serialize_update(update, detail=True)
    return flask.jsonify(data)

# Gets a subreddit recent stylesheet listing
@app.route("/r/<string:subreddit_name>/stylesheets")
def r_subreddit_stylesheets(subreddit_name):
    s = Session()
    stylesheets = s.query(Stylesheet).filter_by(subreddit_name=subreddit_name).order_by(Stylesheet.stylesheet_seq.desc()).limit(10).all()
    data = {"stylesheets": []}
    for ss in stylesheets:
        data["stylesheets"].append(_serialize_stylesheet(ss, detail=False))
    return flask.jsonify(data)

# Gets a stylesheet by ID
@app.route("/stylesheets/<int:stylesheet_id>")
def stylesheet(stylesheet_id):
    s = Session()
    ss = s.query(Stylesheet).get(stylesheet_id)
    data = _serialize_stylesheet(ss, detail=True)
    return flask.jsonify(data)

# Gets a stylesheet by sequence number
@app.route("/r/<string:subreddit_name>/stylesheets/<int:stylesheet_seq>")
def r_subreddit_stylesheet(subreddit_name, stylesheet_seq):
    s = Session()
    ss = s.query(Stylesheet).filter_by(subreddit_name=subreddit_name, stylesheet_seq=stylesheet_seq).one()
    data = _serialize_stylesheet(ss, detail=True)
    return flask.jsonify(data)

# Gets stylesheet CSS by ID
@app.route("/stylesheet/<int:stylesheet_id>/css")
def stylesheet_css(stylesheet_id):
    s = Session()
    ss = s.query(Stylesheet.css).get(stylesheet_id)
    return flask.Response(ss.css, mimetype="text/css")

# Gets stylesheet CSS by sequence number
@app.route("/r/<string:subreddit_name>/stylesheets/<int:stylesheet_seq>/css")
def r_subreddit_stylesheet_css(subreddit_name, stylesheet_seq):
    s = Session()
    ss = s.query(Stylesheet.css).filter_by(subreddit_name=subreddit_name, stylesheet_seq=stylesheet_seq).one()
    return flask.Response(ss.css, mimetype="text/css")
