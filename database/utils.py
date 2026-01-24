import hashlib


def hash_password(password, salt):
    """Hash the given password with the given salt. A hex version of the hash will be returned. Used in all database
    calls for setting/storing user passwords"""

    return hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
