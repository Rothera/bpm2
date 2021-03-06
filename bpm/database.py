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

import json
import os

import arrow

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative
from sqlalchemy import Column, ForeignKey
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy import ForeignKeyConstraint, UniqueConstraint
from sqlalchemy import func
from sqlalchemy.orm import backref, deferred, relationship
from sqlalchemy.orm.exc import NoResultFound

Base = sqlalchemy.ext.declarative.declarative_base()
session_factory = sqlalchemy.orm.sessionmaker()
Session = sqlalchemy.orm.scoped_session(session_factory)

DEFAULT_DATABASE_URI = "postgresql://bpm@/bpm"

def setup_sqlalchemy(database_uri=None, debug=False):
    if database_uri is None:
        database_uri = DEFAULT_DATABASE_URI

    engine = sqlalchemy.create_engine(database_uri, echo=debug)
    Session.configure(bind=engine)
    return engine

def _cleanup_session(exc):
    Session.remove()

def setup_flask(app):
    app.teardown_appcontext(_cleanup_session)

def create_tables(engine):
    Base.metadata.create_all(bind=engine)

def add_database_arguments(parser, debug_default=False):
    parser.add_argument("--database", help="Database URI")
    #parser.add_argument("--nocommit", action="store_true", help="Don't commit")
    if not debug_default:
        parser.add_argument("--database-debug", action="store_true", help="Enable SQLAlchemy debug logs")

def init_from_args(args, debug=None):
    if debug is None:
        debug = args.database_debug
    engine = setup_sqlalchemy(args.database, debug=debug)
    return engine

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
    latest_update_id = Column(Integer)

    # "updates" backref
    # "stylesheets" backref
    latest_update = relationship("Update", foreign_keys=[latest_update_id])

    __table_args__ = (
        ForeignKeyConstraint(
            ["latest_update_id"],
            ["updates.update_id"],
            use_alter=True,
            name="subreddits_latest_update_fkey"),
    )

class Update(Base):
    __tablename__ = "updates"

    update_id = Column(Integer, primary_key=True)
    subreddit_name = Column(String, ForeignKey("subreddits.subreddit_name"), nullable=False)
    update_seq = Column(Integer, nullable=False)
    stylesheet_id = Column(Integer, ForeignKey("stylesheets.stylesheet_id"), nullable=False)
    created = Column(ArrowDateTime(timezone=True), nullable=False)

    subreddit = relationship("Subreddit", backref="updates", foreign_keys=[subreddit_name])
    stylesheet = relationship("Stylesheet", backref="updates")

    __table_args__ = (
        UniqueConstraint("subreddit_name", "update_seq"),
        )

    @classmethod
    def next_update_seq(cls, s, subreddit):
        max = s.query(func.max(cls.update_seq)).filter_by(subreddit_name=subreddit.subreddit_name).one()[0]
        if max is None:
            return 0
        else:
            return max + 1

class Stylesheet(Base):
    __tablename__ = "stylesheets"

    stylesheet_id = Column(Integer, primary_key=True)
    subreddit_name = Column(String, ForeignKey("subreddits.subreddit_name"), nullable=False)
    stylesheet_seq = Column(Integer, nullable=False)
    downloaded = Column(ArrowDateTime(timezone=True), nullable=False)
    css = deferred(Column(String, nullable=False))
    css_hash = Column(String, nullable=False) # hex(sha256(css.encode("utf8")))

    subreddit = relationship("Subreddit", backref="stylesheets", foreign_keys=[subreddit_name])
    # "updates" backref
    # "images" backref
    # "emotes" backref

    __table_args__ = (
        UniqueConstraint("subreddit_name", "stylesheet_seq"),
        )

    @classmethod
    def next_stylesheet_seq(cls, s, subreddit):
        max = s.query(func.max(cls.stylesheet_seq)).filter_by(subreddit_name=subreddit.subreddit_name).one()[0]
        if max is None:
            return 0
        else:
            return max + 1

class Image(Base):
    __tablename__ = "images"

    image_id = Column(Integer, primary_key=True)
    stylesheet_id = Column(Integer, ForeignKey("stylesheets.stylesheet_id"), nullable=False)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    contains_emotes = Column(Boolean, nullable=False)
    filename = Column(String, nullable=False)
    downloaded = Column(ArrowDateTime(timezone=True))

    stylesheet = relationship("Stylesheet", backref="images")

    __table_args__ = (
        UniqueConstraint("stylesheet_id", "name"),
        )

class Emote(Base):
    __tablename__ = "emotes"

    emote_id = Column(Integer, primary_key=True)
    stylesheet_id = Column(Integer, ForeignKey("stylesheets.stylesheet_id"), nullable=False)
    name = Column(String, nullable=False)

    stylesheet = relationship("Stylesheet", backref="emotes")
    # "parts" backref

    __table_args__ = (
        UniqueConstraint("stylesheet_id", "name"),
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

    emote = relationship("Emote", backref=backref("parts", lazy="joined"))

    __table_args__ = (
        UniqueConstraint("emote_id", "specifiers"),
        )

    def serialize(self):
        data = {}
        if self.specifiers:
            data["specifiers"] = json.loads(self.specifiers)
        if self.sprite_image_url:
            sprite = {}
            sprite["image_url"] = self.sprite_image_url
            sprite["x"] = self.sprite_x
            sprite["y"] = self.sprite_y
            sprite["width"] = self.sprite_width
            sprite["height"] = self.sprite_height
            data["sprite"] = sprite
        if self.animation:
            data["animation"] = self.animation
        if self.css:
            data["css"] = json.loads(self.css)
        return data
