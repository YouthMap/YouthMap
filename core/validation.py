import re
from urllib.parse import urlparse

from email_validator import validate_email, EmailNotValidError

CALLSIGN_REGEX = re.compile(r'^[a-z0-9/]{3,15}$', re.IGNORECASE)
PHONE_NUMBER_REGEX = re.compile(r'^[\d\s+\-()]{0,30}$')
HTML_TAG_REGEX = re.compile(r'<[^>]+>')
ALLOWED_URL_SCHEMES = {'http', 'https'}
URL_SLUG_REGEX = re.compile(r'^[a-z0-9\-]+$', re.IGNORECASE)


def contains_html(value: str) -> bool:
    """Return True if the string appears to contain any HTML/XML tag."""

    return bool(HTML_TAG_REGEX.search(value))


def validate_free_text(value: str, field_name: str, max_length: int = 2000):
    """Validate a free-text field. Rejects values that contain HTML tags or exceed max_length.
    Returns (value, None) on success or (None, error_message) on failure."""

    if contains_html(value):
        return None, f"The {field_name} field must not contain HTML."
    if len(value) > max_length:
        return None, f"The {field_name} field must not exceed {max_length} characters."
    return value, None


def validate_callsign(value: str):
    """Validate a callsign. Returns (value.upper(), None) on success or (None, error_message) on failure."""

    value = value.strip()
    if not CALLSIGN_REGEX.match(value):
        return None, "Callsign must be 3–15 characters and contain only letters, numbers, and the stroke character (e.g. G1ABC or G1ABC/P)."
    return value.upper(), None


def validate_email_address(value: str):
    """Validate an email address. Returns (normalised_value, None) on success or (None, error_message) on failure.
    An empty string is permitted (field is optional)."""

    if value == "":
        return value, None
    try:
        info = validate_email(value, check_deliverability=False)
        return info.normalized, None
    except EmailNotValidError as exc:
        return None, f"Email address is not valid: {exc}"


def validate_phone(value: str):
    """Validate a phone number. Returns (value, None) on success or (None, error_message) on failure. An empty string is
     permitted (field is optional)."""

    if value == "":
        return value, None
    if not PHONE_NUMBER_REGEX.match(value):
        return None, "Phone number must contain only digits, spaces, and the characters +, -, and brackets."
    return value, None


def validate_url(value: str, field_name: str = "URL"):
    """Validate a URL, ensuring it uses http or https and does not contain HTML. Returns (value, None) on success or 
    (None, error_message) on failure. An empty string is permitted (field is optional). We pass in a field name such
     as "website" or "QRZ" so that we can generate an error message telling the user where the problem was."""

    if value == "":
        return value, None
    if contains_html(value):
        return None, f"The {field_name} field must not contain HTML."
    try:
        parsed = urlparse(value)
        if parsed.scheme not in ALLOWED_URL_SCHEMES:
            return None, f"The {field_name} must start with http:// or https://."
        if not parsed.netloc:
            return None, f"The {field_name} does not appear to be a valid URL."
    except Exception:
        return None, f"The {field_name} does not appear to be a valid URL."
    return value, None


def validate_url_slug(value: str):
    """Validate a URL slug: letters, numbers, and hyphens only. Returns (value.lower(), None) on success or (None,
     error_message) on failure. An empty string is permitted."""

    value = value.strip().lower()
    if value == "":
        return value, None
    if not URL_SLUG_REGEX.match(value):
        return None, "URL slug must contain only lowercase letters, digits, and hyphens."
    return value, None


def validate_latitude(value: float):
    """Validate a latitude, in degres. Returns (value, None) on success or (None, error_message) on failure."""

    if -90 <= value <= 90:
        return value, None
    else:
        return None, "Latitude must be between -90 and 90 degrees."


def validate_longitude(value: float):
    """Validate a longitude, in degres. Returns (value, None) on success or (None, error_message) on failure."""

    if -180 <= value <= 180:
        return value, None
    else:
        return None, "Longitude must be between -180 and 180 degrees."
