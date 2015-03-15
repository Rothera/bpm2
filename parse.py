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
import bpm.json
import bpm.match

def dump_rules(rules):
    for rule in rules:
        print(rule)

def dump_rules_repr(rules):
    for rule in rules:
        print(repr(rule))

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

        if not special_only or selector.pclasses or selector.prefix or selector.suffix:
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

def main(argv0, argv):
    parser = argparse.ArgumentParser(prog=argv0, description="Parse stylesheet")
    parser.add_argument("--css", action="store_true", help="Dump text rules")
    parser.add_argument("--css-repr", action="store_true", help="Dump repr rules")
    parser.add_argument("--css-json", action="store_true", help="Dump JSON rules")
    parser.add_argument("--emote-selectors", action="store_true", help="Dump emote selector matches")
    parser.add_argument("--emote-specs", action="store_true", help="Dump emote specifiers")
    parser.add_argument("--special", action="store_true", help="Print special emotes only")
    parser.add_argument("stylesheet", help="Stylesheet")

    args = parser.parse_args(argv)

    with open(args.stylesheet) as file:
        css = file.read()

    rules = bpm.css.parse_stylesheet(css)

    if args.css:
        dump_rules(rules)
    elif args.css_repr:
        dump_rules_repr(rules)
    elif args.css_json:
        dump_rules_json(rules)
    elif args.emote_selectors:
        dump_emote_selectors(rules, args.special)
    elif args.emote_specs:
        dump_emote_specifiers(rules, args.special)

if __name__ == "__main__":
    main(sys.argv[0], sys.argv[1:])
