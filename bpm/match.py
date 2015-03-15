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

import enum
import re

import logbook

log = logbook.Logger(__name__)

# Functionality to analyze emote selectors.

class RawSelector:
    def __init__(self, name, pclasses, prefix, suffix):
        self.name = name
        self.pclasses = pclasses # List, possibly empty
        self.prefix = prefix # Something or empty string
        self.suffix = suffix # Something or empty string

    def __repr__(self):
        return "RawSelector(%r, %r, %r, %r)" % (self.name, self.pclasses, self.prefix, self.suffix)

    def __str__(self):
        s = "a[href='%s']" % (self.name)
        s += "".join(self.pclasses)
        if self.prefix:
            s = self.prefix + " " + s
        if self.suffix:
            s = s + " " + self.suffix
        return s

class ThingID:
    type = "thingid"

    def __init__(self, char):
        self.char = char

    def __repr__(self):
        return "ThingID(%r)" % (self.char)

    def __hash__(self):
        return hash(self.char)

    def __eq__(self, other):
        return self.type == other.type and self.char == other.char

    def serialize(self):
        d = {"type": "thingid", "char": self.char}
        return d

class ChildElement:
    type = "childelement"

    def __init__(self, element):
        self.element = element

    def __repr__(self):
        return "ChildElement(%r)" % (self.element)

    def __hash__(self):
        return hash(self.element)

    def __eq__(self, other):
        return self.type == other.type and self.element == other.element

    def serialize(self):
        d = {"type": "childelement", "element": self.element}
        return d

class PseudoClass:
    type = "pclass"

    def __init__(self, pclass):
        self.pclass = pclass

    def __repr__(self):
        return "PseudoClass(%r)" % (self.pclass)

    def __hash__(self):
        return hash(self.pclass)

    def __eq__(self, other):
        return self.type == other.type and self.pclass == other.pclass

    def serialize(self):
        d = {"type": "pclass", "pclass": self.pclass}
        return d

# a[href|="/emote"] is the general case. :hover can go on both the "a" and the
# "]", however, and we also accept arbitrary bits before and after. (Examples
# of those two cases are, respectively, /filly and image macros.)
#
# FIXME: Spaces don't appear to be generally permitted anywhere between the "a"
# and the "[", or after the "]" even if there is a :hover selector immediately
# following. However, Chrome DOES accept spaces in the form :nth-of-type( n ).
# We do not currently handle this case.
#
# FIXME: We may be too accepting around pc2. It's possible for something like
# :hover!suffix to be parsed, strange as it would be.
#
# Permitted emote name characters: [a-zA-Z0-9_:!#/] and must start with / or #
_emote_regexp = re.compile(r"""
    a \s*
    (?P<pclass1>:[\w:\-()]+)? \s*
    \[ \s* href \s* [|^]? = \s* ' (?P<name>[/#][\w:!#\/]+) ' \s* \] \s*
    (?P<pclass2>:[\w:\-()]+)?
    """,
    re.VERBOSE)

# Split up pseudo classes.
_pclass_regexp = re.compile(r"(:+[^:]+)")

def parse_selector(selector):
    selector = re.sub(r"\s+", " ", selector) # Normalize spaces

    # Find ALL a[href] matches in the selector, and then forbid having any more
    # than one.
    m = list(_emote_regexp.finditer(selector))
    if not len(m):
        return None # No emotes here
    elif len(m) > 1:
        log.warning("Multiple emote selectors in {!r}", selector)
        return None
    m = m[0]

    # Take prefix and suffix as pure text, to parse later.
    prefix = selector[:m.start()].strip()
    suffix = selector[m.end():].strip()
    name = m.group("name")

    pclasses = []
    pcs = (m.group("pclass1") or "") + (m.group("pclass2") or "")
    for pc in _pclass_regexp.findall(pcs):
        if pc == ":nth-of-type(n)":
            continue # Drop these; they're useless
        elif pc and pc not in (":hover", ":active"):
            log.warning("Unknown pseudo-class on {!r}: {!r}", selector, pc)
        pclasses.append(pc)

    return RawSelector(name, pclasses, prefix, suffix)

def parse_specifiers(sel):
    specifiers = []
    for pclass in sel.pclasses:
        specifiers.append(_parse_pclass(pclass))
    specifiers.append(_parse_prefix(sel.prefix))
    specifiers.append(_parse_suffix(sel.suffix))
    return [s for s in specifiers if s is not None]

IGNORED_PREFIXES = ["body"]
_thingid_regexp = re.compile(r"""^\.usertext input\[value\$='([a-z0-9])'\] \+ \.usertext-body$""")

CHILD_ELEMENTS = ["em", "strong"]

IGNORED_PCLASSES = [":nth-of-type(n)"]
PSEUDO_CLASSES = [":hover", ":active"]

def _parse_prefix(prefix):
    if not prefix or prefix in IGNORED_PREFIXES:
        return None

    m = _thingid_regexp.match(prefix)
    if m is not None:
        return ThingID(m.group(1))
    else:
        raise ValueError("Unparsable prefix", prefix)

def _parse_suffix(suffix):
    if not suffix:
        return None
    elif suffix in CHILD_ELEMENTS:
        return ChildElement(suffix)
    else:
        raise ValueError("Unparsable suffix", suffix)

def _parse_pclass(pclass):
    if pclass in IGNORED_PCLASSES:
        return None
    elif pclass in PSEUDO_CLASSES:
        return PseudoClass(pclass)
    else:
        raise ValueError("Unparsable pclass", pclass)
