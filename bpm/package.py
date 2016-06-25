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

import arrow

FILE_MAGIC = "rainbow dash is best pony"
FILE_SCHEMA_VERSION = 1

def build_file(filetype, content):
    data = {
        "__betterponymotes_magic": FILE_MAGIC,
        "__betterponymotes_schema": FILE_SCHEMA_VERSION,
        "__betterponymotes_filetype": filetype,
        "__betterponymotes_content": content
    }
    return data
