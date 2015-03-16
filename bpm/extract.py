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

import logbook

log = logbook.Logger(__name__)

import bpm.cssutil
import bpm.match

# Group rules together by emote name and specifiers, collapse rules, find sprite.

class Emote:
    def __init__(self, name, parts):
        self.name = name
        self.parts = parts # frozenset(specifiers) -> [rules]

    def __repr__(self):
        return "Emote(%r, %r)" % (self.name, self.parts)

    def __str__(self):
        if len(self.parts) > 1:
            return "<Emote %s: %s parts>" % (self.name, len(self.parts))
        else:
            return "<Emote %s>" % (self.name)

    def base(self):
        return self.parts[frozenset()]

class EmotePart:
    def __init__(self, specifiers, sprite, css):
        self.specifiers = specifiers
        self.sprite = sprite
        self.css = css

    def __repr__(self):
        return "EmotePart(%r, %r, %r)" % (self.specifiers, self.sprite, self.css)

    def __str__(self):
        flags = []
        if self.specifiers:
            flags.append("complex")
        if self.sprite:
            flags.append("sprite")
        if self.css:
            flags.append("css")
        return "<EmotePart %s>" % (" ".join(flags))

class Sprite:
    def __init__(self, image_url, x, y, width, height):
        self.image_url = image_url
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def __repr__(self):
        return "Sprite(%r, %r, %r, %r, %r)" % (self.image_url, self.x, self.y, self.width, self.height)

    def __str__(self):
        if self.x or self.y:
            return "<Sprite: (%s, %s) at (%s, %s) in %s>" % (self.width, self.height, self.x, self.y, self.image_url)
        else:
            return "<Sprite: (%s, %s) in %s>" % (self.width, self.height, self.image_url)

def filter_ponyscript_ignore(rules):
    ignoring = False

    for rule in rules:
        if rule.type == "rule" and rule.selector == "START-PONYSCRIPT-IGNORE":
            ignoring = True
        elif rule.type == "rule" and rule.selector == "END-PONYSCRIPT-IGNORE":
            ignoring = False
        elif not ignoring:
            yield rule

def group_rules(rules):
    emotes = {} # name -> {frozenset(specifiers) -> [rules]}

    for rule in rules:
        if rule.type != "rule":
            continue

        selector = bpm.match.parse_selector(rule.selector)
        if selector is None:
            # Not an emote.
            continue

        try:
            specifiers = bpm.match.parse_specifiers(selector)
        except ValueError as error:
            log.warning("Specifier parse error: {!r} {!r}", selector, error)
            continue

        key = frozenset(specifiers)

        if selector.name not in emotes:
            emotes[selector.name] = {}
        if key not in emotes[selector.name]:
            emotes[selector.name][key] = []
        emotes[selector.name][key].append(rule)

    return emotes

def collapse_rules(rules):
    props = {}
    important_props = {}

    for rule in rules:
        for p in rule.properties:
            if p.important:
                important_props[p.name] = p.value
            else:
                props[p.name] = p.value

    props.update(important_props)
    return props

def extract_sprite(name, original_css):
    css = original_css.copy()

    # If it's a standard image emote, it should float to the left at a minimum.
    if "float" not in css:
        return (None, original_css)
    else:
        if css["float"].lower() != "left":
            log.warning("{}: Unusual value for float property: {!r}", name, css["float"])
        del css["float"]

    # Find the background image.
    image_url = None
    if "background" in css:
        parts = bpm.cssutil.prop(css.pop("background")).split()
        for p in parts:
            # Ignore everything but the actual image url
            if p.startswith("url("):
                if image_url is not None:
                    log.warning("{}: Multiple images on 'background' property", name)

                image_url = bpm.cssutil.url(p)
            else:
                # Since we remove the property and currently have no way to
                # reassemble all but the image into separate properties,
                # everything else will be discarded.
                log.warning("{}: Discarding extra 'background' component {!r}", name, p)

    if "background-image" in css:
        if image_url is not None:
            log.warning("{}: Both 'background-image' and 'background' properties have images", name)

        # Takes priority over background
        image_url = bpm.cssutil.url(css.pop("background-image"))

    # Need ALL properties to be considered a normal emote. If it isn't, we
    # use NONE of them.
    if image_url is not None and "width" in css and "height" in css:
        # Size
        width = bpm.cssutil.size(css.pop("width"))
        height = bpm.cssutil.size(css.pop("height"))

        # Position
        if "background-position" in css:
            x, y = bpm.cssutil.position(css.pop("background-position"), width, height)
        else:
            x, y = 0, 0

        if x > 0 or y > 0:
            log.warning("{}: Positive background position ({}, {})", name, x, y)
            # No idea what to do here. We'd need the image size to do this
            # correctly.
            x = -abs(x)
            y = -abs(y)

        sprite = Sprite(image_url, x, y, width, height)
        return (sprite, css)
    else:
        return (None, original_css)

IGNORED_CSS_PROPERTIES = ["background-repeat", "clear", "display"]

def clean_css(css):
    # Remove some commonly added useless properties. (Note: some of these
    # we could consider discarding for non-sprite emotes, but lets go the
    # conservative route here.)
    for prop in IGNORED_CSS_PROPERTIES:
        if prop in css:
            del css[prop]

def check_css(name, css):
    # Since it has a sprite, it probably shouldn't have any other CSS
    # (image macros are the exception- lots of spurious warnings on those)
    for (prop, value) in sorted(css.items()):
        log.debug("{}: Unknown extra property {!r}: {!r}", name, prop, value)

def extract_emote(name, group):
    d = {}
    for (key, rules) in group.items():
        css = collapse_rules(rules)
        sprite, css = extract_sprite(name, css)
        if sprite:
            clean_css(css)
            check_css(name, css)
        part = EmotePart(key, sprite, css)
        d[key] = part
    return Emote(name, d)
