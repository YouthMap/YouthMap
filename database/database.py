import hashlib
import secrets
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import IntegrityError

Base = declarative_base()


class User(Base):
    """User model"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    sessions = relationship('Session', back_populates='user')


class Session(Base):
    """Session model"""
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_token = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    expires_at = Column(DateTime, default=datetime.now() + timedelta(hours=24))

    user = relationship('User', back_populates='sessions')


class Database:
    """Data Access Object for the database"""

    def __init__(self, db_path='data/database.db'):
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.init_db()
        self.ensure_default_user()

    def init_db(self):
        """Initialize database with required tables."""
        Base.metadata.create_all(self.engine)

    def ensure_default_user(self):
        """Check if users table is empty and create a default admin user if needed"""

        session = self.SessionLocal()
        try:
            admin_count = session.query(User).count()

            if admin_count == 0:
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

        user_session_token = secrets.token_urlsafe(32)
        session = self.SessionLocal()
        try:
            new_session = Session(
                session_token=user_session_token,
                user_id=user_id
            )
            session.add(new_session)
            session.commit()
            return user_session_token
        except IntegrityError:
            session.rollback()
            return None
        finally:
            session.close()

    def verify_user_session_token(self, session_token):
        """Verify session token is valid and not expired"""

        session = self.SessionLocal()
        try:
            user_session = session.query(Session).filter(
                Session.session_token == session_token,
                Session.expires_at > datetime.now()
            ).first()

            return user_session.user_id if user_session else None
        finally:
            session.close()