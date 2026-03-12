"""Tests for core/utils.py — pure utility functions."""

from datetime import datetime

from core.utils import (
    humanize_start_end,
    generate_password,
    hash_password,
    render_markdown_sanitized,
    to_json_sanitized,
    get_color_for_temp_station,
    get_icon_for_temp_station,
    get_default_event_start_time,
    get_default_event_end_time,
)


# ---------------------------------------------------------------------------
# humanize_start_end
# ---------------------------------------------------------------------------

class TestHumanizeStartEnd:
    def test_same_day_all_day(self):
        start = datetime(2024, 10, 18, 0, 0)
        end = datetime(2024, 10, 18, 23, 59)
        result = humanize_start_end(start, end)
        # Should contain only the date, no time component
        assert "18" in result
        assert "Oct" in result
        assert "2024" in result
        assert "UTC" not in result

    def test_same_day_with_time(self):
        start = datetime(2024, 10, 18, 9, 0)
        end = datetime(2024, 10, 18, 17, 30)
        result = humanize_start_end(start, end)
        assert "09:00" in result
        assert "17:30" in result
        assert "UTC" in result

    def test_same_month_all_day(self):
        start = datetime(2024, 10, 18, 0, 0)
        end = datetime(2024, 10, 20, 23, 59)
        result = humanize_start_end(start, end)
        assert "18" in result
        assert "20" in result
        assert "Oct" in result
        assert "UTC" not in result

    def test_same_month_with_time(self):
        start = datetime(2024, 10, 18, 9, 0)
        end = datetime(2024, 10, 20, 17, 0)
        result = humanize_start_end(start, end)
        assert "09:00" in result
        assert "17:00" in result

    def test_same_year_different_months(self):
        start = datetime(2024, 10, 18, 0, 0)
        end = datetime(2024, 11, 3, 23, 59)
        result = humanize_start_end(start, end)
        assert "Oct" in result
        assert "Nov" in result
        assert "2024" in result

    def test_different_years(self):
        start = datetime(2024, 12, 30, 0, 0)
        end = datetime(2025, 1, 2, 23, 59)
        result = humanize_start_end(start, end)
        assert "2024" in result
        assert "2025" in result


# ---------------------------------------------------------------------------
# generate_password
# ---------------------------------------------------------------------------

class TestGeneratePassword:
    def test_length_is_ten(self):
        pw = generate_password()
        assert len(pw) == 10

    def test_has_lowercase(self):
        pw = generate_password()
        assert any(c.islower() for c in pw)

    def test_has_uppercase(self):
        pw = generate_password()
        assert any(c.isupper() for c in pw)

    def test_has_at_least_three_digits(self):
        pw = generate_password()
        assert sum(c.isdigit() for c in pw) >= 3

    def test_only_alphanumeric(self):
        for _ in range(20):
            pw = generate_password()
            assert pw.isalnum()

    def test_generates_unique_passwords(self):
        passwords = {generate_password() for _ in range(50)}
        # With a 10-char alphanumeric password space, collisions in 50 tries are astronomically unlikely
        assert len(passwords) == 50


# ---------------------------------------------------------------------------
# hash_password
# ---------------------------------------------------------------------------

class TestHashPassword:
    def test_produces_hex_string(self):
        result = hash_password("secret", "somesalt")
        assert isinstance(result, str)
        # SHA-256 = 32 bytes = 64 hex chars
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic(self):
        h1 = hash_password("secret", "somesalt")
        h2 = hash_password("secret", "somesalt")
        assert h1 == h2

    def test_different_password_different_hash(self):
        h1 = hash_password("secret1", "somesalt")
        h2 = hash_password("secret2", "somesalt")
        assert h1 != h2

    def test_different_salt_different_hash(self):
        h1 = hash_password("secret", "salt1")
        h2 = hash_password("secret", "salt2")
        assert h1 != h2


# ---------------------------------------------------------------------------
# render_markdown_sanitized
# ---------------------------------------------------------------------------

class TestRenderMarkdownSanitized:
    def test_basic_paragraph(self):
        result = render_markdown_sanitized("Hello, world!")
        assert "Hello, world!" in result
        assert "<p>" in result

    def test_bold_text(self):
        result = render_markdown_sanitized("**bold**")
        assert "<strong>" in result or "<b>" in result

    def test_script_tag_removed(self):
        result = render_markdown_sanitized("<script>alert(1)</script>")
        assert "<script>" not in result
        assert "alert" not in result

    def test_javascript_link_removed(self):
        result = render_markdown_sanitized("[click me](javascript:alert(1))")
        # javascript: href should be stripped by nh3
        assert "javascript:" not in result

    def test_valid_https_link_preserved(self):
        result = render_markdown_sanitized("[example](https://example.com)")
        assert "https://example.com" in result

    def test_heading_rendered(self):
        result = render_markdown_sanitized("# Title")
        assert "<h1>" in result

    def test_returns_string(self):
        assert isinstance(render_markdown_sanitized("test"), str)


# ---------------------------------------------------------------------------
# to_json_sanitized
# ---------------------------------------------------------------------------

class TestToJsonSanitized:
    def test_basic_dict(self):
        result = to_json_sanitized({"key": "value"})
        assert '"key"' in result
        assert '"value"' in result

    def test_escapes_closing_script_tag(self):
        result = to_json_sanitized({"x": "</script>"})
        assert "</" not in result
        assert r"<\/" in result

    def test_escapes_html_comment(self):
        result = to_json_sanitized({"x": "<!--"})
        assert "<!--" not in result

    def test_list_serialized(self):
        result = to_json_sanitized([1, 2, 3])
        assert "[1, 2, 3]" in result or "[1,2,3]" in result


# ---------------------------------------------------------------------------
# get_color / get_icon for temp station
# ---------------------------------------------------------------------------

class TestTempStationColorIcon:
    def _make_station(self, event=None):
        """Return a minimal mock-like object for a temp station."""

        class FakeStation:
            pass

        s = FakeStation()
        s.event = event
        return s

    def _make_event(self, color, icon):
        class FakeEvent:
            pass

        e = FakeEvent()
        e.color = color
        e.icon = icon
        return e

    def test_color_from_event(self):
        event = self._make_event(color="blue", icon="scouts.png")
        station = self._make_station(event=event)
        assert get_color_for_temp_station(station) == "blue"

    def test_icon_from_event(self):
        event = self._make_event(color="blue", icon="scouts.png")
        station = self._make_station(event=event)
        assert get_icon_for_temp_station(station) == "scouts.png"

    def test_default_color_no_event(self):
        station = self._make_station(event=None)
        assert get_color_for_temp_station(station) == "red"

    def test_default_icon_no_event(self):
        station = self._make_station(event=None)
        assert get_icon_for_temp_station(station) == "radio.png"


# ---------------------------------------------------------------------------
# Default event start/end times
# ---------------------------------------------------------------------------

class TestDefaultEventTimes:
    def test_start_time_is_midnight(self):
        t = get_default_event_start_time()
        assert t.hour == 0
        assert t.minute == 0
        assert t.second == 0

    def test_start_time_is_first_of_month(self):
        t = get_default_event_start_time()
        assert t.day == 1

    def test_end_time_is_end_of_day(self):
        t = get_default_event_end_time()
        assert t.hour == 23
        assert t.minute == 59

    def test_end_time_is_last_day_of_month(self):
        import calendar
        t = get_default_event_end_time()
        days_in_month = calendar.monthrange(t.year, t.month)[1]
        assert t.day == days_in_month

    def test_start_and_end_in_same_month(self):
        start = get_default_event_start_time()
        end = get_default_event_end_time()
        assert start.year == end.year
        assert start.month == end.month
