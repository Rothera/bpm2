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
    def __init__(self, specifiers, sprite, animation, css):
        self.specifiers = specifiers
        self.sprite = sprite
        self.animation = animation
        self.css = css

    def __repr__(self):
        return "EmotePart(%r, %r, %r, %r)" % (self.specifiers, self.sprite, self.animation, self.css)

    def __str__(self):
        flags = []
        if self.specifiers:
            flags.append("complex")
        if self.sprite:
            flags.append("sprite")
        if self.animation:
            flags.append("animation")
        if self.css:
            flags.append("css")
        return "<EmotePart %s>" % (" ".join(flags))

    def serialize_specifiers(self):
        d = [s.serialize() for s in sorted(self.specifiers)]
        return d

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

    def serialize(self):
        return {"image_url": self.image_url, "x": self.x, "y": self.y, "width": self.width, "height": self.height}

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

    # Required emote markers
    if "width" not in css or "height" not in css:
        return (None, original_css)
    if "float" not in css and "display" not in css:
        return (None, original_css)

    # Check for reasonable values
    if "float" in css:
        if css["float"].lower() != "left":
            log.warning("{}: Unusual value for float property: {!r}", name, css["float"])
        del css["float"]

    if "display" in css:
        if css["display"].lower() != "block":
            log.warning("{}: Unusual value for display property: {!r}", name, css["display"])
        del css["display"]

    # Find the background image. One of these is also required.
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
    if image_url is None:
        return (None, original_css)

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

USELESS_PROPERTIES = ["background-repeat", "clear"]

def clean_css(css):
    # Remove some commonly added useless properties. (Note: some of these
    # we could consider discarding for non-sprite emotes, but lets go the
    # conservative route here.)
    for prop in USELESS_PROPERTIES:
        if prop in css:
            del css[prop]

def _vendors(prop):
    return [prop, "-moz-" + prop, "-webkit-" + prop, "-ms-" + prop, "-o-" + prop]

IGNORED_PROPERTIES = _vendors("animation")
IGNORED_PROPERTIES += ["animation-name"]
IGNORED_PROPERTIES += _vendors("transform")

def check_css(name, css):
    # Since it has a sprite, it probably shouldn't have any other CSS
    # (image macros are the exception- lots of spurious warnings on those)
    for (prop, value) in sorted(css.items()):
        if prop not in IGNORED_PROPERTIES:
            log.debug("{}: Unknown extra property {!r}: {!r}", name, prop, value)

def extract_emote(name, group, animations):
    d = {}
    for (key, rules) in group.items():
        css = collapse_rules(rules)
        sprite, css = extract_sprite(name, css)
        animation = extract_animation(css, animations)
        if sprite:
            clean_css(css)
            check_css(name, css)
        part = EmotePart(key, sprite, animation, css)
        d[key] = part
    return Emote(name, d)

def find_animations(rules):
    animations = {}

    for rule in rules:
        if rule.type != "keyframes":
            continue

        animations[rule.name] = rule

    return animations

def find_animation_name(css):
    # Note: No effort to handle multiple conflicting ways fo specify an
    # animation name. We'd probably have to keep properties in declaration
    # order to do so, which isn't worth the bother.
    #
    # Testing in Firefox shows that animations names are case-sensitive.

    if "animation-name" in css:
        return css["animation-name"]

    if "animation" in css:
        attrs = css["animation"].split()
        if attrs:
            return attrs[0]

def extract_animation(css, animations):
    name = find_animation_name(css)
    if name:
        return animations.get(name)
