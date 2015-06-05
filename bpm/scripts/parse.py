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
import bpm.extract
import bpm.json
import bpm.match

def dump_rules(rules, use_repr):
    for rule in rules:
        if use_repr:
            print(repr(rule))
        else:
            print(rule)

def dump_rules_json(rules):
    data = [rule.serialize() for rule in rules]
    json = bpm.json.dumps_config(data, max_depth=3)
    print(json)

def dump_emote_selectors(rules, special_only):
    for rule in rules:
        if rule.type != "rule":
            continue

        selector = bpm.match.parse_selector(rule.selector)
        if selector is None:
            continue

        if special_only and not (selector.pclasses or selector.prefix or selector.suffix):
            continue

        print(repr(selector))

def dump_emote_specifiers(rules, special_only):
    for rule in rules:
        if rule.type != "rule":
            continue

        selector = bpm.match.parse_selector(rule.selector)
        if selector is None:
            continue

        try:
            specifiers = bpm.match.parse_specifiers(selector)
        except ValueError as error:
            print("Error:", selector, repr(error))
            continue

        if specifiers:
            print(selector.name, " ".join(repr(s) for s in specifiers))
        elif not special_only:
            print(selector.name)

def dump_emote_groups(rules, special_only, collapse_rules):
    emotes = bpm.extract.group_rules(rules)

    for (name, parts) in emotes.items():
        for (key, rules) in parts.items():
            if special_only and not len(key):
                continue

            print("Emote:", name)

            if key:
                print("Key:", key)

            if collapse_rules:
                css = bpm.extract.collapse_rules(rules)
                print("Properties:", css)
            else:
                for rule in rules:
                    print("Rule:", rule)
            print()

def dump_emote_sprites(rules, special_only):
    emotes = bpm.extract.group_rules(rules)

    for (name, parts) in emotes.items():
        for (key, rules) in parts.items():
            if special_only and not len(key):
                continue

            css = bpm.extract.collapse_rules(rules)
            sprite, css = bpm.extract.extract_sprite(name, css)

            if sprite is not None:
                bpm.extract.clean_css(css)

                if key:
                    print("%s %s: %s" % (name, key, sprite))
                else:
                    print("%s: %s" % (name, sprite))

                if css:
                    print("- CSS:", css)
            else:
                if key:
                    print("%s %s: %s" % (name, key, css))
                else:
                    print("%s: %s" % (name, css))

def dump_emotes(rules, special_only, use_repr):
    raw_emotes = bpm.extract.group_rules(rules)
    animations = bpm.extract.find_animations(rules)

    for (name, group) in raw_emotes.items():
        emote = bpm.extract.extract_emote(name, group, animations)

        if special_only and len(emote.parts) == 1:
            continue

        if use_repr:
            print(repr(emote))
        else:
            print(emote)

def main(argv0, argv):
    parser = argparse.ArgumentParser(prog=argv0, description="Parse stylesheet")
    parser.add_argument("--css", action="store_true", help="Dump text rules")
    parser.add_argument("--css-repr", action="store_true", help="Dump repr rules")
    parser.add_argument("--css-json", action="store_true", help="Dump JSON rules")
    parser.add_argument("--emote-selectors", action="store_true", help="Dump emote selector matches")
    parser.add_argument("--emote-specs", action="store_true", help="Dump emote specifiers")
    parser.add_argument("--emote-groups", action="store_true", help="Dump emote groups")
    parser.add_argument("--collapse", action="store_true", help="Collapse emote group rules")
    parser.add_argument("--emote-sprites", action="store_true", help="Dump emote sprites")
    parser.add_argument("--emotes", action="store_true", help="Dump emotes")
    parser.add_argument("--emotes-repr", action="store_true", help="Dump repr emotes")

    parser.add_argument("--special", action="store_true", help="Print special emotes only")
    parser.add_argument("--noignore", action="store_true", help="Disregard PONYSCRIPT-IGNORE directives")

    parser.add_argument("stylesheet", help="Stylesheet")

    args = parser.parse_args(argv)

    with open(args.stylesheet) as file:
        css = file.read()

    rules = bpm.css.parse_stylesheet(css)

    if not args.noignore:
        rules = bpm.extract.filter_ponyscript_ignore(rules)

    rules = list(rules) # Force the generator so we can use this multiple times

    if args.css:
        dump_rules(rules, False)
    elif args.css_repr:
        dump_rules(rules, True)
    elif args.css_json:
        dump_rules_json(rules)
    elif args.emote_selectors:
        dump_emote_selectors(rules, args.special)
    elif args.emote_specs:
        dump_emote_specifiers(rules, args.special)
    elif args.emote_groups:
        dump_emote_groups(rules, args.special, args.collapse)
    elif args.emote_sprites:
        dump_emote_sprites(rules, args.special)
    elif args.emotes:
        dump_emotes(rules, args.special, False)
    elif args.emotes_repr:
        dump_emotes(rules, args.special, True)

if __name__ == "__main__":
    main(sys.argv[0], sys.argv[1:])
