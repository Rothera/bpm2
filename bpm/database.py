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

import os

import arrow

import sqlalchemy
from sqlalchemy import Column, ForeignKey
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy import ForeignKeyConstraint, UniqueConstraint
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
Session = sessionmaker()

DEFAULT_DATABASE_URI = "postgresql://bpm@/bpm"

def add_database_arguments(parser):
    parser.add_argument("--database", help="Database URI")
    parser.add_argument("--database-debug", action="store_true", help="Enable SQLAlchemy debug logs")

def lookup_uri(config, args):
    if args.database:
        return args.database
    elif "database" in config:
        return config["database"]
    else:
        return DEFAULT_DATABASE_URI

def init_sqlalchemy(database_uri, debug=False):
    engine = sqlalchemy.create_engine(database_uri, echo=debug)
    Session.configure(bind=engine)
    return engine

def init_from_config(config, args):
    database_uri = lookup_uri(config, args)
    database_debug = config.get("database_debug", args.database_debug)
    engine = init_sqlalchemy(database_uri, debug=database_debug)
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

class Subreddit(Base):
    __tablename__ = "subreddits"

    subreddit_name = Column(String, primary_key=True)

    added = Column(ArrowDateTime(timezone=True), nullable=False)

class Update(Base):
    __tablename__ = "updates"

    update_id = Column(Integer, primary_key=True)

    subreddit_name = Column(String, ForeignKey("subreddits.subreddit_name"), nullable=False)
    update_seq = Column(Integer, nullable=False)

    stylesheet_id = Column(Integer, ForeignKey("stylesheets.stylesheet_id"), nullable=False)
    created = Column(ArrowDateTime(timezone=True), nullable=False)

    @classmethod
    def next_update_seq(cls, s, subreddit):
        max = s.query(func.max(cls.update_seq)).filter_by(subreddit_name=subreddit.subreddit_name).one()[0]
        if max is None:
            return 0
        else:
            return max + 1

    __table_args__ = (
        UniqueConstraint("subreddit_name", "update_seq"),
        )

class Stylesheet(Base):
    __tablename__ = "stylesheets"

    stylesheet_id = Column(Integer, primary_key=True)

    subreddit_name = Column(String, ForeignKey("subreddits.subreddit_name"), nullable=False)
    stylesheet_seq = Column(Integer, nullable=False)

    downloaded = Column(ArrowDateTime(timezone=True), nullable=False)
    css = Column(String, nullable=False)
    css_hash = Column(String, nullable=False) # hex(sha256(css.encode("utf8")))

    @classmethod
    def next_stylesheet_seq(cls, s, subreddit):
        max = s.query(func.max(cls.stylesheet_seq)).filter_by(subreddit_name=subreddit.subreddit_name).one()[0]
        if max is None:
            return 0
        else:
            return max + 1

    __table_args__ = (
        UniqueConstraint("subreddit_name", "stylesheet_seq"),
        )

class Image(Base):
    __tablename__ = "images"

    image_id = Column(Integer, primary_key=True)

    stylesheet_id = Column(Integer, ForeignKey("stylesheets.stylesheet_id"), nullable=False)
    image_name = Column(String, nullable=False)

    image_url = Column(String, nullable=False)
    contains_emotes = Column(Boolean, nullable=False)
    filename = Column(String, nullable=False)
    downloaded = Column(ArrowDateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("stylesheet_id", "image_name"),
        )

class Emote(Base):
    __tablename__ = "emotes"

    emote_id = Column(Integer, primary_key=True)

    stylesheet_id = Column(Integer, ForeignKey("stylesheets.stylesheet_id"), nullable=False)
    emote_name = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("stylesheet_id", "emote_name"),
        )

class EmotePart(Base):
    __tablename__ = "emote_parts"

    part_id = Column(Integer, primary_key=True)

    emote_id = Column(Integer, ForeignKey("emotes.emote_id"), nullable=False)

    # These are all JSON blobs. The sprite is broken out into fields so that
    # they can be queried.
    specifiers = Column(String)

    sprite_image_url = Column(String)
    sprite_x = Column(Integer)
    sprite_y = Column(Integer)
    sprite_width = Column(Integer)
    sprite_height = Column(Integer)

    animation = Column(String)
    css = Column(String)

    __table_args__ = (
        UniqueConstraint("emote_id", "specifiers"),
        )
