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

from setuptools import setup

setup(
    name="bpm",
    version="2.0",
    description="BetterPonymotes",
    packages=["bpm"],
    scripts=[
        "bin/addsubreddit.py",
        "bin/dlimages.py",
        "bin/download.py",
        "bin/initdb.py",
        "bin/manualupdate.py",
        "bin/parse.py",
        "bin/webapi.py"
    ],
    install_requires=[
        "arrow",
        "cssselect",
        "Flask",
        "gunicorn",
        "Logbook",
        "Mako",
        "psycopg2",
        "requests",
        "SQLAlchemy",
        "tinycss2"
    ]
)
