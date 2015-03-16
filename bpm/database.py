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

import sqlalchemy
from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
Session = sessionmaker()

DEFAULT_DATABASE_URI = "postgresql://bpm@/bpm"

def init_sqlalchemy(uri=DEFAULT_DATABASE_URI, debug=False):
    engine = sqlalchemy.create_engine(uri, echo=debug)
    Session.configure(bind=engine)
    return engine

def init_from_config(config, args):
    database_uri = config.get("database", args.database or DEFAULT_DATABASE_URI)
    database_debug = config.get("database_debug", args.database_debug)
    engine = init_sqlalchemy(uri=database_uri, debug=database_debug)
    return engine

def init_tables(engine):
    Base.metadata.create_all(bind=engine)

class ArrowDateTime(sqlalchemy.TypeDecorator):
    impl = sqlalchemy.DateTime
    python_type = arrow.Arrow

    def process_bind_param(self, value, dialect):
        if value is not None:
            return value.datetime
        else:
            return None

    def process_result_value(self, value, dialect):
        if value is not None:
            # PostgreSQL stores in UTC, but we get back a timezone-aware
            # datetime in the system timezone. Convert to UTC internally.
            return arrow.get(value, "utc")
        else:
            return None
