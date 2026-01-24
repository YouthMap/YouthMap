import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Table
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

# Association tables (must be defined first before they are referenced in classes)

temporary_station_bands = Table(
    'temporary_station_bands',
    Base.metadata,
    Column('temporary_station_id', Integer, ForeignKey('temporary_stations.id'), primary_key=True),
    Column('band_id', Integer, ForeignKey('bands.id'), primary_key=True)
)
temporary_station_modes = Table(
    'temporary_station_modes',
    Base.metadata,
    Column('temporary_station_id', Integer, ForeignKey('temporary_stations.id'), primary_key=True),
    Column('mode_id', Integer, ForeignKey('modes.id'), primary_key=True)
)
event_bands = Table(
    'event_bands',
    Base.metadata,
    Column('event_id', Integer, ForeignKey('events.id'), primary_key=True),
    Column('band_id', Integer, ForeignKey('bands.id'), primary_key=True)
)
event_modes = Table(
    'event_modes',
    Base.metadata,
    Column('event_id', Integer, ForeignKey('events.id'), primary_key=True),
    Column('mode_id', Integer, ForeignKey('modes.id'), primary_key=True)
)


# SQLAlchemy Classes

class User(Base):
    """User model"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    sessions = relationship('Session', back_populates='user')


class UserSession(Base):
    """Session model"""
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_token = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    expires_at = Column(DateTime, default=datetime.now() + timedelta(hours=24))

    user = relationship('User', back_populates='sessions')


class PermanentStationType(Base):
    """Permanent station type model"""
    __tablename__ = 'permanent_station_types'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    icon = Column(String, nullable=False)
    color = Column(String, nullable=False)

    stations = relationship('PermanentStation', back_populates='type')

    default_data = [
        {"name": "School", "icon": "book", "color": "yellow"},
        {"name": "University", "icon": "grad-hat", "color": "yellow"},
        {"name": "Cadet", "icon": "beret", "color": "light-blue"}
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
    """Amateur Radio band model"""
    __tablename__ = 'bands'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)

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
    """Amateur Radio mode model"""
    __tablename__ = 'modes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)

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
    """Event model"""
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    icon = Column(String, nullable=False)
    color = Column(String, nullable=False)
    notes_template = Column(String, nullable=False)
    url_slug = Column(String, nullable=True)
    public = Column(Boolean, nullable=False)
    rsgb_event = Column(Boolean, nullable=False)

    stations = relationship('TemporaryStation', back_populates='event')
    bands = relationship('Band', secondary=event_bands, back_populates='events')
    modes = relationship('Mode', secondary=event_modes, back_populates='events')


class TemporaryStation(Base):
    """Temporary Station model"""
    __tablename__ = 'temporary_stations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    callsign = Column(String, nullable=False)
    club_name = Column(String, nullable=False)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    latitude_degrees = Column(Numeric, nullable=False)
    longitude_degrees = Column(Numeric, nullable=False)
    notes = Column(String, nullable=False)
    website_url = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    qrz_url = Column(String, nullable=True)
    social_media_url = Column(String, nullable=True)
    rsgb_attending = Column(Boolean, nullable=False)

    event = relationship('Event', back_populates='stations')
    bands = relationship('Band', secondary=temporary_station_bands, back_populates='temporary_stations')
    modes = relationship('Mode', secondary=temporary_station_modes, back_populates='temporary_stations')


class PermanentStation(Base):
    """Permanent Station model"""
    __tablename__ = 'permanent_stations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    callsign = Column(String, nullable=False)
    club_name = Column(String, nullable=False)
    type_id = Column(Integer, ForeignKey('permanent_station_types.id'), nullable=True)
    latitude_degrees = Column(Numeric, nullable=False)
    longitude_degrees = Column(Numeric, nullable=False)
    meeting_when = Column(String, nullable=False)
    meeting_where = Column(String, nullable=False)
    notes = Column(String, nullable=False)
    website_url = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    qrz_url = Column(String, nullable=True)
    social_media_url = Column(String, nullable=True)

    type = relationship('PermanentStationType', back_populates='stations')


class Database:
    """Data Access Object for the database"""

    def __init__(self, db_path='data/database.db'):
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.init_db()
        self.ensure_default_content()
        self.ensure_default_user()

    def init_db(self):
        """Initialize database with required tables."""
        Base.metadata.create_all(self.engine)

    def ensure_default_content(self):
        """Ensure all default content exists in the database"""

        session = self.SessionLocal()
        try:
            PermanentStationType.initialize(session)
            Band.initialize(session)
            Mode.initialize(session)
        finally:
            session.close()

    def ensure_default_user(self):
        """Check if users table is empty and create a default admin user if needed"""

        session = self.SessionLocal()
        try:
            if session.query(User).count() == 0:
                self.add_user("admin", "password")
        finally:
            session.close()

    def add_user(self, username, password):
        """Create a new user"""

        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()

        session = self.SessionLocal()
        try:
            user = User(
                username=username,
                password_hash=password_hash,
                salt=salt
            )
            session.add(user)
            session.commit()
            return True
        except IntegrityError:
            session.rollback()
            return False
        finally:
            session.close()

    def verify_user(self, username, password):
        """Verify user credentials. If successful, the user ID is returned. Otherwise, None is returned."""

        session = self.SessionLocal()
        try:
            user = session.query(User).filter_by(username=username).first()

            if not user:
                return None

            password_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                user.salt.encode('utf-8'),
                100000
            ).hex()

            if password_hash == user.password_hash:
                return user.id
            return None
        finally:
            session.close()

    def create_user_session(self, user_id):
        """Create a session token for a user. This can then be provided back and verified to ensure they are logged in."""

        # Before we create a new session, clear up any expired ones to keep the database from filling up
        self.cleanup_expired_sessions()

        user_session_token = secrets.token_urlsafe(32)
        session = self.SessionLocal()
        try:
            new_user_session = UserSession(
                session_token=user_session_token,
                user_id=user_id
            )
            session.add(new_user_session)
            session.commit()
            return user_session_token
        except IntegrityError:
            session.rollback()
            return None
        finally:
            session.close()

    def verify_user_session_token(self, session_token):
        """Verify session token is valid and not expired. Return the session ID if one exists, otherwise None."""

        session = self.SessionLocal()
        try:
            user_session = session.query(UserSession).filter(
                UserSession.session_token == session_token,
                UserSession.expires_at > datetime.now()
            ).first()

            return user_session.user_id if user_session else None
        finally:
            session.close()

    def cleanup_expired_sessions(self):
        """Housekeeping method to delete all expired sessions from the database. Returns True if successful, False otherwise."""

        session = self.SessionLocal()
        try:
            for user_session in session.query(UserSession).filter(UserSession.expires_at <= datetime.now()).all():
                session.delete(user_session)
            session.commit()
            return True
        except IntegrityError:
            session.rollback()
            return False
        finally:
            session.close()

    def add_event(self, name, start_time, end_time, icon, color, notes_template, bands, modes,
                  url_slug=None, public=True, rsgb_event=False):
        """Create a new event. Returns the event ID if one was created."""

        session = self.SessionLocal()
        try:
            event = Event(
                name=name,
                start_time=start_time,
                end_time=end_time,
                icon=icon,
                color=color,
                notes_template=notes_template,
                url_slug=url_slug,
                public=public,
                rsgb_event=rsgb_event
            )
            event.bands.extend(bands)
            event.modes.extend(modes)
            session.add(event)
            session.commit()
            return event.id
        except IntegrityError:
            session.rollback()
            return None
        finally:
            session.close()

    def get_bands_by_name(self, band_names):
        """Converts a list of string band names into Band objects to use with the database."""

        session = self.SessionLocal()
        try:
            return [session.query(Band).filter_by(name=b).first() for b in band_names]
        finally:
            session.close()

    def get_modes_by_name(self, mode_names):
        """Converts a list of string mode names into Mode objects to use with the database."""

        session = self.SessionLocal()
        try:
            return [session.query(Mode).filter_by(name=b).first() for b in mode_names]
        finally:
            session.close()
