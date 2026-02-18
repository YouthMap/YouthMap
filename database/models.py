import secrets
from datetime import datetime, timedelta

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric
from sqlalchemy.orm import relationship

from .base import Base, temporary_station_bands, temporary_station_modes, event_bands, event_modes
from .utils import hash_password


class Config(Base):
    """Application config model. Stores things like SMTP credentials, reCAPTCHA key, etc. Implemented in the database
    rather than in plain config files to allow the config to be edited without messing with config files, which gets
    messy in Docker-based setups. However, note that some information (e.g. the HTTP port and path to the database) must
    still be implemented in file-based config, as they are needed before the user could get to modify this."""

    __tablename__ = 'config'

    id = Column(Integer, primary_key=True)
    base_url = Column(String, nullable=True)
    enable_mail = Column(Boolean, nullable=False)
    mail_sender = Column(String, nullable=True)
    mail_username = Column(String, nullable=True)
    mail_password = Column(String, nullable=True)
    mail_server_host = Column(String, nullable=True)
    mail_server_port = Column(Integer, nullable=True)
    enable_captcha = Column(Boolean, nullable=False)
    recaptcha_key = Column(String, nullable=True)

    @classmethod
    def initialize(cls, session):
        """Initialize the database with a config row if one doesn't exist"""

        existing = session.query(cls).first()
        if not existing:
            session.add(cls(enable_mail=False, enable_captcha=False))
        session.commit()


class User(Base):
    """User model. Stores their username, encrypted password, email address, super-admin status etc."""

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    super_admin = Column(Boolean, nullable=False)

    # Link the users with the sessions, so we can find all sessions relating to the user. We supply 'delete-orphan' to
    # the 'cascade' parameter here so that if we delete a user, all orphaned sessions that were linked to that user will
    # be deleted too.
    sessions = relationship('UserSession', back_populates='user', cascade='all, delete-orphan')

    @classmethod
    def initialize(cls, session):
        """Initialize the database with a default admin user (password 'password') if no users exist"""
        if session.query(cls).count() == 0:
            salt = secrets.token_hex(32)
            password_hash = hash_password("password", salt)
            session.add(cls(username="admin", password_hash=password_hash, salt=salt, super_admin=True))


class UserSession(Base):
    """User session model. Stores a token generated to authenticate the user."""

    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_token = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    expires_at = Column(DateTime, default=datetime.now() + timedelta(hours=24))

    # Link the sessions with the users, so we can find the user that owns this session.
    user = relationship('User', back_populates='sessions')


class PermanentStationType(Base):
    """Permanent station type model. Stores information on the School, University and Cadet types of permanent station."""

    __tablename__ = 'permanent_station_types'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    icon = Column(String, nullable=False)
    color = Column(String, nullable=False)

    # Link the type with the permanent stations, so we can get a list of the permanent stations that have this type.
    stations = relationship('PermanentStation', back_populates='type')

    default_data = [
        {"name": "School", "icon": "school.png", "color": "yellow"},
        {"name": "University", "icon": "uni.png", "color": "orange"},
        {"name": "Cadet", "icon": "cadets.png", "color": "lightblue"}
    ]

    @classmethod
    def initialize(cls, session):
        """Initialize the database with the station types if they don't exist"""

        for station_type in cls.default_data:
            existing = session.query(cls).filter_by(name=station_type["name"]).first()
            if not existing:
                session.add(cls(name=station_type["name"], icon=station_type["icon"], color=station_type["color"]))
        session.commit()


class Band(Base):
    """Amateur Radio band model. Stores the bands we can assign to events and stations."""

    __tablename__ = 'bands'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)

    # Link the band with the events and temporary stations, so we can get a list of the events and temporary stations
    # that use this band.
    events = relationship('Event', secondary=event_bands, back_populates='bands')
    temporary_stations = relationship('TemporaryStation', secondary=temporary_station_bands, back_populates='bands')

    default_data = ["2200m", "600m", "160m", "80m", "60m", "40m", "30m", "20m", "17m", "15m", "12m", "11m", "10m", "6m",
                    "5m", "4m", "2m", "1.25m", "70cm", "23cm", "13cm", "5.8GHz", "10GHz", "24GHz", "47GHz", "76GHz"]

    @classmethod
    def initialize(cls, session):
        """Initialize the database with the band names if they don't exist"""

        for band in cls.default_data:
            existing = session.query(cls).filter_by(name=band).first()
            if not existing:
                session.add(cls(name=band))
        session.commit()


class Mode(Base):
    """Amateur Radio mode model. Stores the modes we can assign to events and stations."""

    __tablename__ = 'modes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)

    # Link the mode with the events and temporary stations, so we can get a list of the events and temporary stations
    # that use this mode.
    events = relationship('Event', secondary=event_modes, back_populates='modes')
    temporary_stations = relationship('TemporaryStation', secondary=temporary_station_modes, back_populates='modes')

    default_data = ["CW", "Phone", "Data"]

    @classmethod
    def initialize(cls, session):
        """Initialize the database with the mode names if they don't exist"""

        for mode in cls.default_data:
            existing = session.query(cls).filter_by(name=mode).first()
            if not existing:
                session.add(cls(name=mode))
        session.commit()


class Event(Base):
    """Event model. An event represents something like 'JOTA' or 'Field Day' to which temporary stations can be assigned."""

    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    icon = Column(String, nullable=False)
    color = Column(String, nullable=False)
    notes_template = Column(String, nullable=False)
    url_slug = Column(String, unique=True, nullable=False)
    public = Column(Boolean, nullable=False)
    rsgb_event = Column(Boolean, nullable=False)

    # Link the event to the temporary stations that use it, so we can fetch them. We supply 'delete-orphan' to the
    # 'cascade' parameter here so that if we delete an event, all orphaned temporary stations that were linked to that
    # event will be deleted too.
    stations = relationship('TemporaryStation', back_populates='event', cascade='all, delete-orphan')
    # Link the event to the bands and modes it will use, via an association table.
    bands = relationship('Band', secondary=event_bands, back_populates='events')
    modes = relationship('Mode', secondary=event_modes, back_populates='events')


class TemporaryStation(Base):
    """Temporary Station model. A temporary station represents an amateur radio station that is taking part in event,
    or, if no event is assigned, then it is a generic Special Event Station for an event that is not known to the system."""

    __tablename__ = 'temporary_stations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    callsign = Column(String, nullable=False)
    club_name = Column(String, nullable=False)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    latitude_degrees = Column(Numeric, nullable=False)
    longitude_degrees = Column(Numeric, nullable=False)
    notes = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    qrz_url = Column(String, nullable=True)
    social_media_url = Column(String, nullable=True)
    rsgb_attending = Column(Boolean, nullable=False)
    approved = Column(Boolean, nullable=False)
    edit_password = Column(String, nullable=False)

    # Link the temporary station to the event it is for.
    event = relationship('Event', back_populates='stations')
    # Link the temporary station to the bands and modes it will use, via an association table.
    bands = relationship('Band', secondary=temporary_station_bands, back_populates='temporary_stations')
    modes = relationship('Mode', secondary=temporary_station_modes, back_populates='temporary_stations')


class PermanentStation(Base):
    """Permanent Station model. This represents an amateur radio station permanently based at a school, university or
    cadet base."""

    __tablename__ = 'permanent_stations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    callsign = Column(String, nullable=False)
    club_name = Column(String, nullable=False)
    type_id = Column(Integer, ForeignKey('permanent_station_types.id'), nullable=True)
    latitude_degrees = Column(Numeric, nullable=False)
    longitude_degrees = Column(Numeric, nullable=False)
    meeting_when = Column(String, nullable=False)
    meeting_where = Column(String, nullable=False)
    notes = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    qrz_url = Column(String, nullable=True)
    social_media_url = Column(String, nullable=True)
    approved = Column(Boolean, nullable=False)
    edit_password = Column(String, nullable=False)

    # Link the permanent station to its type.
    type = relationship('PermanentStationType', back_populates='stations')
