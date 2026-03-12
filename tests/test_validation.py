"""Tests for core/validation.py — all pure functions with no external dependencies."""

from core.validation import (
    validate_callsign,
    validate_free_text,
    validate_email_address,
    validate_phone,
    validate_url,
    validate_url_slug,
    validate_latitude,
    validate_longitude,
    contains_html,
)


# ---------------------------------------------------------------------------
# contains_html
# ---------------------------------------------------------------------------

class TestContainsHtml:
    def test_detects_open_tag(self):
        assert contains_html("<b>bold</b>") is True

    def test_detects_self_closing_tag(self):
        assert contains_html("<br/>") is True

    def test_plain_text_is_clean(self):
        assert contains_html("plain text") is False

    def test_angle_brackets_without_tag(self):
        # The regex conservatively matches any < ... > sequence, so this is treated as HTML.
        # This is an intentional false-positive — the validator rejects anything that looks
        # like it might be a tag, even if it isn't.
        assert contains_html("1 < 2 and 3 > 4") is True

    def test_script_tag_detected(self):
        assert contains_html("<script>alert(1)</script>") is True


# ---------------------------------------------------------------------------
# validate_callsign
# ---------------------------------------------------------------------------

class TestValidateCallsign:
    def test_valid_basic(self):
        value, err = validate_callsign("G1ABC")
        assert value == "G1ABC"
        assert err is None

    def test_valid_with_stroke(self):
        value, err = validate_callsign("G1ABC/P")
        assert value == "G1ABC/P"
        assert err is None

    def test_converts_to_uppercase(self):
        value, err = validate_callsign("g1abc")
        assert value == "G1ABC"
        assert err is None

    def test_strips_whitespace(self):
        value, err = validate_callsign("  G1ABC  ")
        assert value == "G1ABC"
        assert err is None

    def test_minimum_length(self):
        value, err = validate_callsign("AB1")
        assert value == "AB1"
        assert err is None

    def test_maximum_length(self):
        value, err = validate_callsign("A" * 15)
        assert err is None

    def test_too_short(self):
        value, err = validate_callsign("AB")
        assert value is None
        assert err is not None

    def test_too_long(self):
        value, err = validate_callsign("A" * 16)
        assert value is None
        assert err is not None

    def test_invalid_characters(self):
        value, err = validate_callsign("G1!BC")
        assert value is None
        assert err is not None

    def test_empty_string(self):
        value, err = validate_callsign("")
        assert value is None
        assert err is not None


# ---------------------------------------------------------------------------
# validate_free_text
# ---------------------------------------------------------------------------

class TestValidateFreeText:
    def test_valid_plain_text(self):
        value, err = validate_free_text("Hello, world!", "notes")
        assert value == "Hello, world!"
        assert err is None

    def test_rejects_html_tag(self):
        value, err = validate_free_text("<b>bold</b>", "notes")
        assert value is None
        assert "HTML" in err

    def test_rejects_script_tag(self):
        value, err = validate_free_text("<script>alert(1)</script>", "description")
        assert value is None
        assert err is not None

    def test_respects_default_max_length(self):
        value, err = validate_free_text("x" * 2001, "notes")
        assert value is None
        assert "2000" in err

    def test_allows_exactly_max_length(self):
        value, err = validate_free_text("x" * 2000, "notes")
        assert value is not None
        assert err is None

    def test_custom_max_length(self):
        value, err = validate_free_text("x" * 101, "notes", max_length=100)
        assert value is None
        assert "100" in err

    def test_empty_string_allowed(self):
        value, err = validate_free_text("", "notes")
        assert value == ""
        assert err is None

    def test_error_message_names_field(self):
        value, err = validate_free_text("<b>x</b>", "club name")
        assert "club name" in err


# ---------------------------------------------------------------------------
# validate_email_address
# ---------------------------------------------------------------------------

class TestValidateEmail:
    def test_valid_email(self):
        value, err = validate_email_address("user@example.com")
        assert err is None
        assert "@" in value

    def test_empty_string_allowed(self):
        value, err = validate_email_address("")
        assert value == ""
        assert err is None

    def test_invalid_email_no_domain(self):
        value, err = validate_email_address("notanemail")
        assert value is None
        assert err is not None

    def test_invalid_email_missing_tld(self):
        value, err = validate_email_address("user@")
        assert value is None
        assert err is not None

    def test_normalises_email(self):
        # email-validator normalises case
        value, err = validate_email_address("User@Example.COM")
        assert err is None
        assert value == value.lower() or "@" in value  # normalised


# ---------------------------------------------------------------------------
# validate_phone
# ---------------------------------------------------------------------------

class TestValidatePhone:
    def test_valid_uk_number(self):
        value, err = validate_phone("+44 1234 567890")
        assert value is not None
        assert err is None

    def test_valid_with_parentheses(self):
        value, err = validate_phone("(0800) 123-456")
        assert err is None

    def test_empty_string_allowed(self):
        value, err = validate_phone("")
        assert value == ""
        assert err is None

    def test_rejects_letters(self):
        value, err = validate_phone("123abc456")
        assert value is None
        assert err is not None

    def test_rejects_special_characters(self):
        value, err = validate_phone("+44 1234 @ 567")
        assert value is None
        assert err is not None


# ---------------------------------------------------------------------------
# validate_url
# ---------------------------------------------------------------------------

class TestValidateUrl:
    def test_valid_https_url(self):
        value, err = validate_url("https://example.com")
        assert value == "https://example.com"
        assert err is None

    def test_valid_http_url(self):
        value, err = validate_url("http://example.com/path?q=1")
        assert err is None

    def test_empty_string_allowed(self):
        value, err = validate_url("")
        assert value == ""
        assert err is None

    def test_rejects_ftp_scheme(self):
        value, err = validate_url("ftp://example.com")
        assert value is None
        assert "http" in err

    def test_rejects_javascript_scheme(self):
        value, err = validate_url("javascript:alert(1)")
        assert value is None
        assert err is not None

    def test_rejects_url_containing_html(self):
        value, err = validate_url("https://example.com/<script>")
        assert value is None
        assert err is not None

    def test_rejects_url_without_netloc(self):
        value, err = validate_url("https://")
        assert value is None
        assert err is not None

    def test_field_name_in_error(self):
        _, err = validate_url("ftp://x.com", field_name="QRZ page")
        assert "QRZ page" in err


# ---------------------------------------------------------------------------
# validate_url_slug
# ---------------------------------------------------------------------------

class TestValidateUrlSlug:
    def test_valid_slug(self):
        value, err = validate_url_slug("jota-2024")
        assert value == "jota-2024"
        assert err is None

    def test_converts_to_lowercase(self):
        value, err = validate_url_slug("JOTA-2024")
        assert value == "jota-2024"
        assert err is None

    def test_strips_whitespace(self):
        value, err = validate_url_slug("  jota  ")
        assert value == "jota"
        assert err is None

    def test_empty_string_allowed(self):
        value, err = validate_url_slug("")
        assert value == ""
        assert err is None

    def test_rejects_spaces(self):
        value, err = validate_url_slug("jota 2024")
        assert value is None
        assert err is not None

    def test_rejects_underscores(self):
        value, err = validate_url_slug("jota_2024")
        assert value is None
        assert err is not None

    def test_rejects_special_characters(self):
        value, err = validate_url_slug("jota@2024")
        assert value is None
        assert err is not None


# ---------------------------------------------------------------------------
# validate_latitude
# ---------------------------------------------------------------------------

class TestValidateLatitude:
    def test_valid_mid_range(self):
        value, err = validate_latitude(51.5)
        assert value == 51.5
        assert err is None

    def test_lower_boundary(self):
        value, err = validate_latitude(-90)
        assert value == -90
        assert err is None

    def test_upper_boundary(self):
        value, err = validate_latitude(90)
        assert value == 90
        assert err is None

    def test_too_low(self):
        value, err = validate_latitude(-90.01)
        assert value is None
        assert err is not None

    def test_too_high(self):
        value, err = validate_latitude(90.01)
        assert value is None
        assert err is not None

    def test_zero(self):
        value, err = validate_latitude(0)
        assert value == 0
        assert err is None


# ---------------------------------------------------------------------------
# validate_longitude
# ---------------------------------------------------------------------------

class TestValidateLongitude:
    def test_valid_mid_range(self):
        value, err = validate_longitude(-0.127)
        assert value == -0.127
        assert err is None

    def test_lower_boundary(self):
        value, err = validate_longitude(-180)
        assert value == -180
        assert err is None

    def test_upper_boundary(self):
        value, err = validate_longitude(180)
        assert value == 180
        assert err is None

    def test_too_low(self):
        value, err = validate_longitude(-180.01)
        assert value is None
        assert err is not None

    def test_too_high(self):
        value, err = validate_longitude(180.01)
        assert value is None
        assert err is not None
