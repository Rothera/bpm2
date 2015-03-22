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
import hashlib
import json
import sys

import arrow

import bpm.css
import bpm.database
import bpm.extract
import bpm.images
import bpm.scripts

def extract_emotes(rules):
    raw_emotes = bpm.extract.group_rules(rules)
    animations = bpm.extract.find_animations(rules)

    emotes = {}

    for (name, group) in raw_emotes.items():
        emote = bpm.extract.extract_emote(name, group, animations)
        emotes[name] = emote

    return emotes

def find_spritesheets(emotes):
    spritesheets = set()

    for (name, emote) in emotes.items():
        for part in emote.parts.values():
            if part.sprite:
                url = part.sprite.image_url
                assert url.startswith("%%") and url.endswith("%%")
                spritesheets.add(url[2:-2])

    return spritesheets

def main(argv0, argv):
    parser = argparse.ArgumentParser(prog=argv0, description="Manually create subreddit update")
    bpm.database.add_database_arguments(parser)
    bpm.scripts.add_config_arguments(parser)
    parser.add_argument("-n", action="store_true", help="Don't commit")
    parser.add_argument("--noignore", action="store_true", help="Disregard PONYSCRIPT-IGNORE directives")
    parser.add_argument("subreddit", help="Subreddit")
    parser.add_argument("stylesheet", help="Stylesheet")
    parser.add_argument("images", help="Images file")

    args = parser.parse_args(argv)
    config = bpm.scripts.load_config(argv0, args)
    engine = bpm.database.init_from_config(config, args)

    now = arrow.utcnow()

    with open(args.stylesheet) as file:
        css = file.read()

    css_hash = hashlib.sha256(css.encode("utf8")).hexdigest()

    rules = bpm.css.parse_stylesheet(css)
    if not args.noignore:
        rules = bpm.extract.filter_ponyscript_ignore(rules)

    rules = list(rules) # Force the generator so we can use this multiple times

    emotes = extract_emotes(rules)
    spritesheets = find_spritesheets(emotes)

    with open(args.images) as file:
        images = json.load(file)

    # All database access is conditional on -n to avoid errors using this script
    # on subreddits that aren't in the table.
    if not args.n:
        s = bpm.database.Session()

        subreddit = s.query(bpm.database.Subreddit).get(args.subreddit)

        # Add stylesheet
        stylesheet_seq = bpm.database.Stylesheet.next_stylesheet_seq(s, subreddit)
        stylesheet = bpm.database.Stylesheet(
            subreddit_name=args.subreddit,
            stylesheet_seq=stylesheet_seq,
            downloaded=now,
            css=css,
            css_hash=css_hash)

        # Partial commit to get stylesheet_id
        s.begin_nested()
        s.add(stylesheet)
        s.commit()

        # Add all images.
        for (name, url) in sorted(images.items()):
            filename = bpm.images.image_filename(url)
            contains_emotes = name in spritesheets
            image = bpm.database.Image(
                    stylesheet_id=stylesheet.stylesheet_id,
                    image_name=name,
                    image_url=url,
                    contains_emotes=contains_emotes,
                    filename=filename)
            s.add(image)

        # Add all emotes (not parts). One big partial commit to get emote ID's.
        s.begin_nested()
        emote_rows = {}
        for (name, emote) in sorted(emotes.items()):
            e = bpm.database.Emote(stylesheet_id=stylesheet.stylesheet_id, emote_name=name)
            emote_rows[name] = e
            s.add(e)
        s.commit()

        for (name, emote) in sorted(emotes.items()):
            for (specifiers, part) in sorted(emote.parts.items()):
                specifiers_json = json.dumps(part.serialize_specifiers()) if part.specifiers else None
                css_json = json.dumps(part.css, sort_keys=True) if part.css else None

                p = bpm.database.EmotePart(
                    emote_id=emote_rows[name].emote_id,
                    specifiers=specifiers_json,
                    animation=part.animation,
                    css=css_json)

                if part.sprite:
                    p.sprite_image_url = part.sprite.image_url
                    p.sprite_x = part.sprite.x
                    p.sprite_y = part.sprite.y
                    p.sprite_width = part.sprite.width
                    p.sprite_height = part.sprite.height

                s.add(p)

        # Add update
        seq = bpm.database.Update.next_update_seq(s, subreddit)
        update = bpm.database.Update(subreddit_name=args.subreddit, update_seq=seq, stylesheet_id=stylesheet.stylesheet_id, created=now)
        s.add(update)

        s.commit()

if __name__ == "__main__":
    main(sys.argv[0], sys.argv[1:])
