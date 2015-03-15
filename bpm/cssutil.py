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

def prop(text):
    return " ".join(text.replace("!important", "").split())

def size(text):
    # Parses a single size declaration. Meant to be used on width/height
    # properties.
    #
    # This should always be measured in pixels, though "0px" is often abbreviated
    # to just "0".
    return _size(prop(text))

def position(text, width, height):
    x_text, y_text = prop(text).split()
    return (_pos(x_text, width), _pos(y_text, height))

def url(text):
    text = prop(text)
    if text.startswith("url(") and text.endswith(")"):
        return text[4:-1].strip().strip("'\"")
    raise ValueError("Invalid URL", text)

def _size(s):
    if s.endswith("px"):
        s = s[:-2]
    return int(s)

def _pos(s, size):
    # Hack to handle percentage values, which are essentially multiples of the
    # width/height.
    if s[-1] == "%":
        # Non-multiples of 100 won't work too well here (but who would do that?)
        return int(int(s[:-1]) / 100.0 * size)
    else:
        # Value is generally negative, though there are some odd exceptions.
        return _size(s)
