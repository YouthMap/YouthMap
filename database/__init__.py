from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import DATABASE_DIR
from .base import Base
from .models import User, UserSession, Event, TemporaryStation, PermanentStation, Band, Mode, PermanentStationType, \
    Config
from .operations import DatabaseOperations


class Database(DatabaseOperations):
    """Data Access Object for the database"""

    def __init__(self):
        # Create database directory if it doesn't already exist
        Path(DATABASE_DIR).mkdir(parents=True, exist_ok=True)

        # Create DB and session factory
        self.engine = create_engine('sqlite:///' + DATABASE_DIR + "/database.db")
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Initialize parent class with session factory
        super().__init__(self.SessionLocal)

        # Initialize the database
        self.init_db()

        # Populate with default content if necessary
        self.ensure_default_content()

    def init_db(self):
        """Initialize database with required tables."""

        Base.metadata.create_all(self.engine)

    def ensure_default_content(self):
        """Ensure all default content exists in the database.
        This sets up a default config for the application, plus the enum-like tables such as bands, modes and permanent
        station types."""

        session = self.SessionLocal()
        try:
            Config.initialize(session)
            User.initialize(session)
            PermanentStationType.initialize(session)
            Band.initialize(session)
            Mode.initialize(session)
        finally:
            session.close()


__all__ = ['Database', 'Config', 'User', 'UserSession', 'Event', 'TemporaryStation', 'PermanentStation', 'Band', 'Mode',
           'PermanentStationType']
