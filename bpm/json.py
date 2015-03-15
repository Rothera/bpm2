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

"""
A JSON encoder designed to produce beautiful output.

The dump()/dumps() methods defined here accept a few options that the standard
json encoder does not, useful for formatting output JSON data in particularly
nice ways, depending on the data.

The "indent" parameter means the same as it does to the standard library: lists
and dictionaries will have their entries indended by that amount. None disables
indentation completely.

"split_lists" defines whether or not to put newlines after each comma-separated
value in lists and dictionaries.

"max_depth" is the maximum object nesting depth at which the encoder will
generate newlines. Deeper objects will always be put on a single line. The top-
level object has a depth of 1, so a max_depth=1 parameter will indent the first
level of items and no more.
"""

import json
from json import load, loads # For convenience
import sys

# Code taken from json module and modified.
def _encode(obj, indent, split_lists, max_depth, sort_keys):
    if max_depth is not None:
        max_depth += 1
    def _encode_obj(obj, depth):
        if isinstance(obj, str):
            # Because who cares about portability
            yield json.encoder.encode_basestring_ascii(obj)
        elif obj is None:
            yield "null"
        elif obj is True:
            yield "true"
        elif obj is False:
            yield "false"
        elif isinstance(obj, int):
            yield str(obj)
        elif isinstance(obj, (tuple, list)):
            for chunk in _encode_list(obj, depth):
                yield chunk
        elif isinstance(obj, dict):
            for chunk in _encode_dict(obj, depth):
                yield chunk
        else:
            raise TypeError("Can't encode %r" % (obj))

    def _encode_list(obj, depth):
        if not obj:
            yield "[]"
            return
        if indent is None or (max_depth is not None and depth >= max_depth):
            yield "["
        else:
            yield "[\n" + (depth * indent * " ")
        first = True
        for item in obj:
            if first:
                first = False
            else:
                if indent is not None and split_lists and (max_depth is None or depth < max_depth):
                    yield ",\n" + (depth * indent * " ")
                else:
                    yield ", "
            for chunk in _encode_obj(item, depth + 1):
                yield chunk
        if indent is None or (max_depth is not None and depth >= max_depth):
            yield "]"
        else:
            yield "\n" + ((depth - 1) * indent * " ") + "]"

    def _encode_dict(obj, depth):
        if not obj:
            yield "{}"
            return
        if indent is None or (max_depth is not None and depth >= max_depth):
            yield "{"
        else:
            yield "{\n" + (depth * indent * " ")
        first = True
        if sort_keys:
            keys = sorted(obj)
        else:
            keys = obj
        for key in keys:
            value = obj[key]
            if first:
                first = False
            else:
                if indent is not None and split_lists and (max_depth is None or depth < max_depth):
                    yield ",\n" + (depth * indent * " ")
                else:
                    yield ", "
            # Keys must be strings
            if key is None:
                key = "null"
            elif key is True:
                key = "true"
            elif key is False:
                key = "false"
            elif isinstance(key, int):
                key = str(key)
            for chunk in _encode_obj(key, depth + 1):
                yield chunk
            yield ": "
            for chunk in _encode_obj(value, depth + 1):
                yield chunk
        if indent is None or (max_depth is not None and depth >= max_depth):
            yield "}"
        else:
            yield "\n" + ((depth - 1) * indent * " ") + "}"

    return _encode_obj(obj, 1)

def dump(root, file, indent=None, split_lists=True, max_depth=None, sort_keys=False):
    for chunk in _encode(root, indent, split_lists, max_depth, sort_keys):
        file.write(chunk)

def dumps(root, indent=None, split_lists=True, max_depth=None, sort_keys=False):
    return "".join(list(_encode(root, indent, split_lists, max_depth, sort_keys)))

# BPM standard JSON format
def dump_config(root, file, max_depth=1):
    dump(root, file, indent=2, split_lists=True, max_depth=max_depth, sort_keys=True)
    file.write("\n")

def dumps_config(root, max_depth=1):
    return dumps(root, indent=2, split_lists=True, max_depth=max_depth, sort_keys=True) + "\n"
