import hashlib
import logging
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
    """User model. Stores their username, encrypted password, email address, super-admin status etc."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    super_admin = Column(Boolean, nullable=False)

    # Link the users with the sessions, so we can find all sessions relating to the user. We supply 'delete-orphan' to
    # the 'cascade' parameter here so that if we delete a user, all orphaned sessions that were linked to that user will
    # be deleted too.
    sessions = relationship('UserSession', back_populates='user', cascade='all, delete-orphan')


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
    url_slug = Column(String, unique=True, nullable=True)
    public = Column(Boolean, nullable=False)
    rsgb_event = Column(Boolean, nullable=False)

    # Link the event to the temporary stations that use it, so we can fetch them.  We supply 'delete-orphan' to the
    # 'cascade' parameter here so that if we delete an event, all orphaned temporary stations that were linked to that
    # event will be deleted too.
    stations = relationship('TemporaryStation', back_populates='event', cascade='all, delete-orphan')
    # Link the event to the bands and modes it will use, via an association table.
    bands = relationship('Band', secondary=event_bands, back_populates='events')
    modes = relationship('Mode', secondary=event_modes, back_populates='events')


class TemporaryStation(Base):
    """Temporary Station model. A temporary station represents an amateur ratio station that is taking part in event,
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
    notes = Column(String, nullable=False)
    website_url = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    qrz_url = Column(String, nullable=True)
    social_media_url = Column(String, nullable=True)
    rsgb_attending = Column(Boolean, nullable=False)

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
    notes = Column(String, nullable=False)
    website_url = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    qrz_url = Column(String, nullable=True)
    social_media_url = Column(String, nullable=True)

    # Link the permanent station to its type.
    type = relationship('PermanentStationType', back_populates='stations')


class Database:
    """Data Access Object for the database"""

    def __init__(self):
        # Create DB and session factory
        self.engine = create_engine(f'sqlite:///data/database.db')
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Initialise the database
        self.init_db()

        # Populate with default content
        self.ensure_default_content()
        self.ensure_default_user()

    def init_db(self):
        """Initialize database with required tables."""
        Base.metadata.create_all(self.engine)

    def ensure_default_content(self):
        """Ensure all default content exists in the database. This sets up the enum-like tables such as bands, modes
        and permanent station types."""

        session = self.SessionLocal()
        try:
            PermanentStationType.initialize(session)
            Band.initialize(session)
            Mode.initialize(session)
        finally:
            session.close()

    def ensure_default_user(self):
        """Check if users table is empty and create a default admin user if so. This provides something that the user
        can log in with on first run, before they create proper accounts."""

        session = self.SessionLocal()
        try:
            if session.query(User).count() == 0:
                self.add_user("admin", "password", None, True)
        finally:
            session.close()

    def add_user(self, username, password, email, super_admin):
        """Create a new user"""

        # Create a new salt and hash the password with it so we have something safe to store
        salt = secrets.token_hex(32)
        password_hash = self.hash_password(password, salt)

        session = self.SessionLocal()
        try:
            # Store the new user info in the database.
            user = User(
                username=username,
                password_hash=password_hash,
                salt=salt,
                email=email,
                super_admin=super_admin
            )
            session.add(user)
            session.commit()
            return True
        except IntegrityError as e:
            logging.error("Error when adding user", e)
            session.rollback()
            return False
        finally:
            session.close()

    def get_user(self, user_id):
        """Get a user by ID. Returns the User object if found, otherwise None."""

        session = self.SessionLocal()
        try:
            return session.query(User).filter_by(id=user_id).first()
        finally:
            session.close()

    def get_all_users(self):
        """Get all users. Returns a list of User objects."""

        session = self.SessionLocal()
        try:
            return session.query(User).all()
        finally:
            session.close()

    def update_user(self, user_id, username=None, password=None, email=None, super_admin=None):
        """Update an existing user. Only provided fields will be updated. Returns True if successful."""

        session = self.SessionLocal()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return False

            if username is not None:
                user.username = username
            if password is not None:
                # Create a new salt and hash the password
                salt = secrets.token_hex(32)
                user.salt = salt
                user.password_hash = self.hash_password(password, salt)
            if email is not None:
                user.email = email
            if super_admin is not None:
                user.super_admin = super_admin

            session.commit()
            return True
        except IntegrityError as e:
            logging.error("Error when updating user", e)
            session.rollback()
            return False
        finally:
            session.close()

    def delete_user(self, user_id):
        """Delete a user and all associated sessions. Returns True if successful."""

        session = self.SessionLocal()
        try:
            # Find the user
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return False

            # Delete the user. Our use of "cascade='delete-orphan'" when linking the session and user tables together
            # ensures that any sessions belonging to the user will automatically be deleted.
            session.delete(user)

            session.commit()
            return True
        except IntegrityError as e:
            logging.error("Error when deleting user", e)
            session.rollback()
            return False
        finally:
            session.close()

    def verify_user(self, username, password):
        """Verify user credentials. If successful, the user ID is returned. Otherwise, None is returned."""

        session = self.SessionLocal()
        try:
            # Find the user matching the username (if there is one)
            user = session.query(User).filter_by(username=username).first()
            if not user:
                return None

            # Get the stored salt for the user, and hash the provided password with it
            password_hash = self.hash_password(password, user.salt)

            # If the hashes match, the password was correct and we can log in
            if password_hash == user.password_hash:
                return user.id
            return None
        finally:
            session.close()

    def create_user_session(self, user_id):
        """Create a session token for a user. This can then be provided back and verified to ensure they are logged in."""

        # Before we create a new session, clear up any expired ones to keep the database from filling up
        self.cleanup_expired_sessions()

        # Generate a token
        user_session_token = secrets.token_urlsafe(32)

        # Store the token in the database so we can later verify against it
        session = self.SessionLocal()
        try:
            new_user_session = UserSession(
                session_token=user_session_token,
                user_id=user_id
            )
            session.add(new_user_session)
            session.commit()
            return user_session_token
        except IntegrityError as e:
            logging.error("Error when creating session", e)
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
        except IntegrityError as e:
            logging.error("Error when clearing up expired sessions", e)
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
        except IntegrityError as e:
            logging.error("Error when adding event", e)
            session.rollback()
            return None
        finally:
            session.close()

    def get_event(self, event_id):
        """Get an event by ID. Returns the Event object if found, otherwise None."""

        session = self.SessionLocal()
        try:
            return session.query(Event).filter_by(id=event_id).first()
        finally:
            session.close()

    def get_all_events(self):
        """Get all events. Returns a list of Event objects."""

        session = self.SessionLocal()
        try:
            return session.query(Event).all()
        finally:
            session.close()

    def update_event(self, event_id, name=None, start_time=None, end_time=None, icon=None,
                     color=None, notes_template=None, bands=None, modes=None, url_slug=None,
                     public=None, rsgb_event=None):
        """Update an existing event. Only provided fields will be updated. Returns True if successful."""

        session = self.SessionLocal()
        try:
            event = session.query(Event).filter_by(id=event_id).first()
            if not event:
                return False

            if name is not None:
                event.name = name
            if start_time is not None:
                event.start_time = start_time
            if end_time is not None:
                event.end_time = end_time
            if icon is not None:
                event.icon = icon
            if color is not None:
                event.color = color
            if notes_template is not None:
                event.notes_template = notes_template
            if url_slug is not None:
                event.url_slug = url_slug
            if public is not None:
                event.public = public
            if rsgb_event is not None:
                event.rsgb_event = rsgb_event
            if bands is not None:
                event.bands = bands
            if modes is not None:
                event.modes = modes

            session.commit()
            return True
        except IntegrityError as e:
            logging.error("Error when updating event", e)
            session.rollback()
            return False
        finally:
            session.close()

    def delete_event(self, event_id):
        """Delete an event and all associated temporary stations. Returns True if successful."""

        session = self.SessionLocal()
        try:
            event = session.query(Event).filter_by(id=event_id).first()
            if not event:
                return False

            # Delete the event. The cascade='delete-orphan' option provided at creation of the schema ensures temporary
            # stations are deleted alongside it.
            session.delete(event)
            session.commit()
            return True
        except IntegrityError as e:
            logging.error("Error when deleting event", e)
            session.rollback()
            return False
        finally:
            session.close()

    def add_temporary_station(self, callsign, club_name, start_time, end_time,
                              latitude_degrees, longitude_degrees, notes, bands, modes,
                              event_id=None, website_url=None, email=None, phone_number=None,
                              qrz_url=None, social_media_url=None, rsgb_attending=False):
        """Create a new temporary station. Returns the station ID if creation was successful, otherwise None."""

        session = self.SessionLocal()
        try:
            station = TemporaryStation(
                callsign=callsign,
                club_name=club_name,
                event_id=event_id,
                start_time=start_time,
                end_time=end_time,
                latitude_degrees=latitude_degrees,
                longitude_degrees=longitude_degrees,
                notes=notes,
                website_url=website_url,
                email=email,
                phone_number=phone_number,
                qrz_url=qrz_url,
                social_media_url=social_media_url,
                rsgb_attending=rsgb_attending
            )
            station.bands.extend(bands)
            station.modes.extend(modes)

            session.add(station)
            session.commit()
            return station.id
        except IntegrityError as e:
            logging.error("Error when adding temporary station", e)
            session.rollback()
            return None
        finally:
            session.close()

    def get_temporary_station(self, station_id):
        """Get a temporary station by ID. Returns the TemporaryStation object if found, otherwise None."""

        session = self.SessionLocal()
        try:
            return session.query(TemporaryStation).filter_by(id=station_id).first()
        finally:
            session.close()

    def get_all_temporary_stations(self):
        """Get all temporary stations. Returns a list of TemporaryStation objects."""

        session = self.SessionLocal()
        try:
            return session.query(TemporaryStation).all()
        finally:
            session.close()

    def get_temporary_stations_by_event(self, event_id):
        """Get all temporary stations for a specific event. Returns a list of TemporaryStation objects."""

        session = self.SessionLocal()
        try:
            return session.query(TemporaryStation).filter_by(event_id=event_id).all()
        finally:
            session.close()

    def update_temporary_station(self, station_id, callsign=None, club_name=None, event_id=None,
                                 start_time=None, end_time=None, latitude_degrees=None,
                                 longitude_degrees=None, notes=None, bands=None, modes=None,
                                 website_url=None, email=None, phone_number=None, qrz_url=None,
                                 social_media_url=None, rsgb_attending=None):
        """Update an existing temporary station. Only provided fields will be updated. Returns True if successful."""

        session = self.SessionLocal()
        try:
            station = session.query(TemporaryStation).filter_by(id=station_id).first()
            if not station:
                return False

            if callsign is not None:
                station.callsign = callsign
            if club_name is not None:
                station.club_name = club_name
            if event_id is not None:
                station.event_id = event_id
            if start_time is not None:
                station.start_time = start_time
            if end_time is not None:
                station.end_time = end_time
            if latitude_degrees is not None:
                station.latitude_degrees = latitude_degrees
            if longitude_degrees is not None:
                station.longitude_degrees = longitude_degrees
            if notes is not None:
                station.notes = notes
            if website_url is not None:
                station.website_url = website_url
            if email is not None:
                station.email = email
            if phone_number is not None:
                station.phone_number = phone_number
            if qrz_url is not None:
                station.qrz_url = qrz_url
            if social_media_url is not None:
                station.social_media_url = social_media_url
            if rsgb_attending is not None:
                station.rsgb_attending = rsgb_attending
            if bands is not None:
                station.bands = bands
            if modes is not None:
                station.modes = modes

            session.commit()
            return True
        except IntegrityError as e:
            logging.error("Error when updating temporary station", e)
            session.rollback()
            return False
        finally:
            session.close()

    def delete_temporary_station(self, station_id):
        """Delete a temporary station. Returns True if successful."""

        session = self.SessionLocal()
        try:
            station = session.query(TemporaryStation).filter_by(id=station_id).first()
            if not station:
                return False

            session.delete(station)
            session.commit()
            return True
        except IntegrityError as e:
            logging.error("Error when deleting temporary station", e)
            session.rollback()
            return False
        finally:
            session.close()

    def add_permanent_station(self, callsign, club_name, latitude_degrees, longitude_degrees,
                              meeting_when, meeting_where, notes, type_id=None, website_url=None,
                              email=None, phone_number=None, qrz_url=None, social_media_url=None):
        """Create a new permanent station. Returns the station ID if creation was successful, otherwise None."""

        session = self.SessionLocal()
        try:
            station = PermanentStation(
                callsign=callsign,
                club_name=club_name,
                type_id=type_id,
                latitude_degrees=latitude_degrees,
                longitude_degrees=longitude_degrees,
                meeting_when=meeting_when,
                meeting_where=meeting_where,
                notes=notes,
                website_url=website_url,
                email=email,
                phone_number=phone_number,
                qrz_url=qrz_url,
                social_media_url=social_media_url
            )

            session.add(station)
            session.commit()
            return station.id
        except IntegrityError as e:
            logging.error("Error when adding permanent station", e)
            session.rollback()
            return None
        finally:
            session.close()

    def get_permanent_station(self, station_id):
        """Get a permanent station by ID. Returns the PermanentStation object if found, otherwise None."""

        session = self.SessionLocal()
        try:
            return session.query(PermanentStation).filter_by(id=station_id).first()
        finally:
            session.close()

    def get_all_permanent_stations(self):
        """Get all permanent stations. Returns a list of PermanentStation objects."""

        session = self.SessionLocal()
        try:
            return session.query(PermanentStation).all()
        finally:
            session.close()

    def get_permanent_stations_by_type(self, type_id):
        """Get all permanent stations of a specific type. Returns a list of PermanentStation objects."""

        session = self.SessionLocal()
        try:
            return session.query(PermanentStation).filter_by(type_id=type_id).all()
        finally:
            session.close()

    def update_permanent_station(self, station_id, callsign=None, club_name=None, type_id=None,
                                 latitude_degrees=None, longitude_degrees=None, meeting_when=None,
                                 meeting_where=None, notes=None, website_url=None, email=None,
                                 phone_number=None, qrz_url=None, social_media_url=None):
        """Update an existing permanent station. Only provided fields will be updated. Returns True if successful."""

        session = self.SessionLocal()
        try:
            station = session.query(PermanentStation).filter_by(id=station_id).first()
            if not station:
                return False

            if callsign is not None:
                station.callsign = callsign
            if club_name is not None:
                station.club_name = club_name
            if type_id is not None:
                station.type_id = type_id
            if latitude_degrees is not None:
                station.latitude_degrees = latitude_degrees
            if longitude_degrees is not None:
                station.longitude_degrees = longitude_degrees
            if meeting_when is not None:
                station.meeting_when = meeting_when
            if meeting_where is not None:
                station.meeting_where = meeting_where
            if notes is not None:
                station.notes = notes
            if website_url is not None:
                station.website_url = website_url
            if email is not None:
                station.email = email
            if phone_number is not None:
                station.phone_number = phone_number
            if qrz_url is not None:
                station.qrz_url = qrz_url
            if social_media_url is not None:
                station.social_media_url = social_media_url

            session.commit()
            return True
        except IntegrityError as e:
            logging.error("Error when updating permanent station", e)
            session.rollback()
            return False
        finally:
            session.close()

    def delete_permanent_station(self, station_id):
        """Delete a permanent station. Returns True if successful."""

        session = self.SessionLocal()
        try:
            station = session.query(PermanentStation).filter_by(id=station_id).first()
            if not station:
                return False

            session.delete(station)
            session.commit()
            return True
        except IntegrityError as e:
            logging.error("Error when deleting permanent station", e)
            session.rollback()
            return False
        finally:
            session.close()

    def get_permanent_station_type_by_name(self, type_name):
        """Get a permanent station type by name. Returns the PermanentStationType object if found, otherwise None."""

        session = self.SessionLocal()
        try:
            return session.query(PermanentStationType).filter_by(name=type_name).first()
        finally:
            session.close()

    def get_all_permanent_station_types(self):
        """Get all permanent station types. Returns a list of PermanentStationType objects."""

        session = self.SessionLocal()
        try:
            return session.query(PermanentStationType).all()
        finally:
            session.close()

    def get_all_bands(self):
        """Get all bands. Returns a list of Band objects."""

        session = self.SessionLocal()
        try:
            return session.query(Band).all()
        finally:
            session.close()

    def get_all_modes(self):
        """Get all modes. Returns a list of Mode objects."""

        session = self.SessionLocal()
        try:
            return session.query(Mode).all()
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

    def hash_password(self, password, salt):
        """Hash the given password with the given salt. A hex version of the hash will be returned."""

        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
