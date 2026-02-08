import logging
import secrets
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from .models import (
    User, UserSession,
    Event,
    TemporaryStation, PermanentStation,
    Band, Mode, PermanentStationType
)
from .utils import hash_password, generate_password


class DatabaseOperations:
    """Base class containing all database CRUD operations"""

    def __init__(self, session_factory):
        """Initialize with a SQLAlchemy session factory"""
        self.SessionLocal = session_factory

    def add_user(self, username, password, email, super_admin):
        """Create a new user"""

        # Create a new salt and hash the password with it so we have something safe to store
        salt = secrets.token_hex(32)
        password_hash = hash_password(password, salt)

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
            return user.id
        except IntegrityError as e:
            logging.error("Error when adding user", e)
            session.rollback()
            return None
        finally:
            session.close()

    def get_user(self, user_id):
        """Get a user by ID. Returns the User object if found, otherwise None."""

        session = self.SessionLocal()
        try:
            return session.query(User).options(joinedload(User.sessions)).filter_by(id=user_id).first()
        finally:
            session.close()

    def get_all_users(self):
        """Get all users. Returns a list of User objects."""

        session = self.SessionLocal()
        try:
            return session.query(User).options(joinedload(User.sessions)).all()
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
                user.password_hash = hash_password(password, salt)
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
            password_hash = hash_password(password, user.salt)

            # If the hashes match, the password was correct and we can log in
            if password_hash == user.password_hash:
                return user.id
            return None
        finally:
            session.close()

    def is_insecure_user_present(self):
        """Returns true if the users table contains an entry with username 'admin' and password 'password'. Used to
        show a warning in the UI."""
        return self.verify_user('admin', 'password') is not None

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
        """Verify session token is valid and not expired. Return the user ID if valid, otherwise None."""

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

    def get_permanent_station_type(self, type_id):
        """Get a permanent station type by ID. Returns the PermanentStationType object if found, otherwise None."""

        session = self.SessionLocal()
        try:
            return session.query(PermanentStationType).options(joinedload(PermanentStationType.stations)).filter_by(
                id=type_id).first()
        finally:
            session.close()
            
    def add_event(self, name, start_time, end_time, icon, color, notes_template, band_ids, mode_ids,
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

            # Add selected bands and modes to the station. Because these are lists of bands and modes, and stored in an
            # association table, we can't just set them at object creation time using SQLalchemy, so we add them here.
            bands = [session.query(Band).filter_by(id=id).first() for id in band_ids]
            modes = [session.query(Mode).filter_by(id=id).first() for id in mode_ids]
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
            return session.query(Event).options(joinedload(Event.stations), joinedload(Event.bands),
                                                joinedload(Event.modes)).filter_by(id=event_id).first()
        finally:
            session.close()

    def get_all_events(self):
        """Get all events. Returns a list of Event objects."""

        session = self.SessionLocal()
        try:
            return session.query(Event).options(joinedload(Event.stations), joinedload(Event.bands),
                                                joinedload(Event.modes)).all()
        finally:
            session.close()

    def update_event(self, event_id, name=None, start_time=None, end_time=None, icon=None,
                     color=None, notes_template=None, band_ids=None, mode_ids=None, url_slug=None,
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
            if band_ids is not None:
                bands = [session.query(Band).filter_by(id=id).first() for id in band_ids]
                event.bands.clear()
                event.bands.extend(bands)
            if mode_ids is not None:
                modes = [session.query(Mode).filter_by(id=id).first() for id in mode_ids]
                event.modes.clear()
                event.modes.extend(modes)

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

    def cleanup_expired_events(self):
        """Delete all expired events from the database. Any orphaned Temporary Stations will also be deleted. Returns
        True if successful, False otherwise."""

        session = self.SessionLocal()
        try:
            for event in session.query(Event).filter(Event.end_time <= datetime.now()).all():
                session.delete(event)
            session.commit()
            return True
        except IntegrityError as e:
            logging.error("Error when clearing up expired events", e)
            session.rollback()
            return False
        finally:
            session.close()

    def add_temporary_station(self, callsign, club_name, start_time, end_time,
                              latitude_degrees, longitude_degrees, notes, band_ids, mode_ids,
                              event_id=None, website_url=None, email=None, phone_number=None,
                              qrz_url=None, social_media_url=None, rsgb_attending=False, approved=False):
        """Create a new temporary station. Returns the station ID if creation was successful, otherwise None. If
        creation was successful, the new object contains an automatically generated edit_password which should be
        provided to the visitor to allow editing it in future without being logged in. Stations can be created with the
        approved flag set either true or false, this should be true if a logged-in user created it or false if a visitor
        created it, at which point it is not displayed until a proper user logs in and sets it to approved."""

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
                rsgb_attending=rsgb_attending,
                approved=approved
            )

            # Add selected bands and modes to the station. Because these are lists of bands and modes, and stored in an
            # association table, we can't just set them at object creation time using SQLalchemy, so we add them here.
            bands = [session.query(Band).filter_by(id=id).first() for id in band_ids]
            modes = [session.query(Mode).filter_by(id=id).first() for id in mode_ids]
            station.bands.extend(bands)
            station.modes.extend(modes)

            # Generate an "edit password" to allow a visitor to update the station they created without having to be a
            # logged-in user
            station.edit_password = generate_password()

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
            return session.query(TemporaryStation).options(joinedload(TemporaryStation.event),
                                                           joinedload(TemporaryStation.bands),
                                                           joinedload(TemporaryStation.modes)).filter_by(
                id=station_id).first()
        finally:
            session.close()

    def get_all_temporary_stations(self):
        """Get all temporary stations. Returns a list of TemporaryStation objects."""

        session = self.SessionLocal()
        try:
            return session.query(TemporaryStation).options(
                joinedload(TemporaryStation.event), joinedload(TemporaryStation.bands),
                joinedload(TemporaryStation.modes)).all()
        finally:
            session.close()

    def get_temporary_stations_by_event(self, event_id):
        """Get all temporary stations for a specific event. Returns a list of TemporaryStation objects."""

        session = self.SessionLocal()
        try:
            return session.query(TemporaryStation).options(joinedload(TemporaryStation.event),
                                                           joinedload(TemporaryStation.bands),
                                                           joinedload(TemporaryStation.modes)).filter_by(
                event_id=event_id).all()
        finally:
            session.close()

    def update_temporary_station(self, station_id, callsign=None, club_name=None, event_id=None,
                                 start_time=None, end_time=None, latitude_degrees=None,
                                 longitude_degrees=None, notes=None, band_ids=None, mode_ids=None,
                                 website_url=None, email=None, phone_number=None, qrz_url=None,
                                 social_media_url=None, rsgb_attending=None, approved=None, edit_password=None):
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
            if band_ids is not None:
                bands = [session.query(Band).filter_by(id=id).first() for id in band_ids]
                station.bands.clear()
                station.bands.extend(bands)
            if mode_ids is not None:
                modes = [session.query(Mode).filter_by(id=id).first() for id in mode_ids]
                station.modes.clear()
                station.modes.extend(modes)
            if approved is not None:
                station.approved = approved
            if edit_password is not None:
                station.edit_password = edit_password

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

    def cleanup_expired_temporary_stations(self):
        """Delete all expired temporary stations from the database. This will not delete any Events they were
        associated with, even if those events have also expired. Returns True if successful, False otherwise."""

        session = self.SessionLocal()
        try:
            for ts in session.query(TemporaryStation).filter(TemporaryStation.end_time <= datetime.now()).all():
                session.delete(ts)
            session.commit()
            return True
        except IntegrityError as e:
            logging.error("Error when clearing up expired temporary stations", e)
            session.rollback()
            return False
        finally:
            session.close()

    def add_permanent_station(self, callsign, club_name, latitude_degrees, longitude_degrees,
                              meeting_when, meeting_where, notes, type_id=None, website_url=None,
                              email=None, phone_number=None, qrz_url=None, social_media_url=None, approved=False):
        """Create a new permanent station. Returns the station ID if creation was successful, otherwise None. If
        creation was successful, the new object contains an automatically generated edit_password which should be
        provided to the visitor to allow editing it in future without being logged in. Stations can be created with the
        approved flag set either true or false, this should be true if a logged-in user created it or false if a visitor
        created it, at which point it is not displayed until a proper user logs in and sets it to approved."""

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
                social_media_url=social_media_url,
                approved=approved
            )

            # Generate an "edit password" to allow a visitor to update the station they created without having to be a
            # logged-in user
            station.edit_password = generate_password()

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
            return session.query(PermanentStation).options(joinedload(PermanentStation.type)).filter_by(
                id=station_id).first()
        finally:
            session.close()

    def get_all_permanent_stations(self):
        """Get all permanent stations. Returns a list of PermanentStation objects."""

        session = self.SessionLocal()
        try:
            return session.query(PermanentStation).options(joinedload(PermanentStation.type)).all()
        finally:
            session.close()

    def get_permanent_stations_by_type(self, type_id):
        """Get all permanent stations of a specific type. Returns a list of PermanentStation objects."""

        session = self.SessionLocal()
        try:
            return session.query(PermanentStation).options(joinedload(PermanentStation.type)).filter_by(
                type_id=type_id).all()
        finally:
            session.close()

    def update_permanent_station(self, station_id, callsign=None, club_name=None, type_id=None,
                                 latitude_degrees=None, longitude_degrees=None, meeting_when=None,
                                 meeting_where=None, notes=None, website_url=None, email=None,
                                 phone_number=None, qrz_url=None, social_media_url=None, approved=None,
                                 edit_password=None):
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
            if approved is not None:
                station.approved = approved
            if edit_password is not None:
                station.edit_password = edit_password

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
