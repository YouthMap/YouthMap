import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta


class Database:
    """Data Access Object for the database"""

    def __init__(self, db_path='data/database.db'):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        """Get a connection to the database"""

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize database with required tables."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_token TEXT UNIQUE NOT NULL,
                admin_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (admin_id) REFERENCES admins (id)
            )
        ''')

        conn.commit()
        conn.close()

    def add_admin(self, username, password):
        """Create a new admin user"""

        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                'INSERT INTO admins (username, password_hash, salt) VALUES (?, ?, ?)',
                (username, password_hash, salt)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def verify_admin(self, username, password):
        """Verify admin credentials"""

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            'SELECT id, password_hash, salt FROM admins WHERE username = ?',
            (username,)
        )
        result = cursor.fetchone()
        conn.close()

        if not result:
            return None

        stored_hash = result['password_hash']
        salt = result['salt']

        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()

        if password_hash == stored_hash:
            return result['id']
        return None

    def create_session(self, admin_id, duration_hours=24):
        """Create a session token for an administrator"""

        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=duration_hours)

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            'INSERT INTO sessions (session_token, admin_id, expires_at) VALUES (?, ?, ?)',
            (session_token, admin_id, expires_at)
        )

        conn.commit()
        conn.close()

        return session_token

    def verify_session(self, session_token):
        """Verify session token is valid and not expired"""

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            'SELECT admin_id FROM sessions WHERE session_token = ? AND expires_at > ?',
            (session_token, datetime.now())
        )
        result = cursor.fetchone()
        conn.close()

        return result['admin_id'] if result else None
