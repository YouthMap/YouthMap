import hashlib
import secrets
import string


def generate_password():
    """Generate a password-like string. This is used to generate both the 'edit password' that visitors are given to
    allow them to edit stations they submitted, and when a super-admin creates a new account for someome else. The
    generated password is 10 characters long and contains at least one lowercase letter, uppercase letter, and number."""

    alphabet = string.ascii_letters + string.digits
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(10))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and sum(c.isdigit() for c in password) >= 3):
            return password


def hash_password(password, salt):
    """Hash the given password with the given salt. A hex version of the hash will be returned. Used in all database
    calls for setting/storing user passwords"""

    return hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
