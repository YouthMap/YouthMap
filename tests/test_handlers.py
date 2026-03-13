"""Tests for Tornado request handlers — runs a live in-process HTTP server."""

from datetime import datetime, timedelta

import tornado.testing
import tornado.web

from requesthandlers.admin import AdminHandler
from requesthandlers.contact import ContactHandler
from requesthandlers.login import LoginHandler
from requesthandlers.logout import LogoutHandler
from requesthandlers.map import MapHandler
from requesthandlers.pendingstations import PendingStationsHandler
from requesthandlers.viewstation import ViewStationHandler
from tests.conftest import make_test_db


def _future():
    return datetime.now() + timedelta(days=365)


def make_app(db):
    """Build a minimal Tornado application wired to the given database."""
    app = tornado.web.Application(
        [
            (r"/", MapHandler),
            (r"/view/station/(perm|temp)/([^/]+)", ViewStationHandler),
            (r"/pending", PendingStationsHandler),
            (r"/contact", ContactHandler),
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
            (r"/admin", AdminHandler),
            # Slug route — must come last, same as in youthmap.py
            (r"/([^/]+)", MapHandler),
        ],
        template_path="templates",
        cookie_secret="test-cookie-secret",
        login_url="/login",
        # Disable XSRF so tests can POST without tokens
        xsrf_cookies=False,
    )
    app.db = db
    return app


# ---------------------------------------------------------------------------
# Map handler
# ---------------------------------------------------------------------------

class TestMapHandler(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        return make_app(make_test_db())

    def test_homepage_returns_200(self):
        response = self.fetch("/")
        self.assertEqual(response.code, 200)

    def test_homepage_contains_html(self):
        response = self.fetch("/")
        self.assertIn(b"<!DOCTYPE html>", response.body)

    def test_unknown_slug_redirects_home(self):
        response = self.fetch("/no-such-slug", follow_redirects=False)
        self.assertEqual(response.code, 302)
        self.assertIn("/", response.headers.get("Location", ""))


# ---------------------------------------------------------------------------
# Pending stations handler
# ---------------------------------------------------------------------------

class TestPendingStationsHandler(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        self.db = make_test_db()
        return make_app(self.db)

    def test_returns_200(self):
        response = self.fetch("/pending")
        self.assertEqual(response.code, 200)

    def test_empty_message_when_no_pending(self):
        response = self.fetch("/pending")
        self.assertIn(b"no stations", response.body.lower())

    def test_shows_pending_temp_station(self):
        self.db.add_temporary_station(
            callsign="G1PND", club_name="Pending Club",
            start_time=datetime.now(), end_time=_future(),
            latitude_degrees=51.5, longitude_degrees=-0.1,
            notes="", band_ids=[], mode_ids=[],
            approved=False,
        )
        response = self.fetch("/pending")
        self.assertEqual(response.code, 200)
        self.assertIn(b"G1PND", response.body)
        self.assertIn(b"Pending Club", response.body)

    def test_shows_pending_perm_station(self):
        school_type_id = next(t for t in self.db.get_all_permanent_station_types() if t.name == "School").id
        self.db.add_permanent_station(
            callsign="G1PRX", club_name="Perm Pending",
            latitude_degrees=51.5, longitude_degrees=-0.1,
            meeting_when="Tuesdays", meeting_where="Clubhouse",
            notes="", approved=False, type_id=school_type_id,
        )
        response = self.fetch("/pending")
        self.assertEqual(response.code, 200)
        self.assertIn(b"G1PRX", response.body)

    def test_does_not_show_approved_station(self):
        self.db.add_temporary_station(
            callsign="G1APV", club_name="Approved Club",
            start_time=datetime.now(), end_time=_future(),
            latitude_degrees=51.5, longitude_degrees=-0.1,
            notes="", band_ids=[], mode_ids=[],
            approved=True,
        )
        response = self.fetch("/pending")
        self.assertNotIn(b"G1APV", response.body)

    def test_pending_station_links_to_view_page(self):
        sid = self.db.add_temporary_station(
            callsign="G1LNK", club_name="Link Club",
            start_time=datetime.now(), end_time=_future(),
            latitude_degrees=51.5, longitude_degrees=-0.1,
            notes="", band_ids=[], mode_ids=[],
            approved=False,
        )
        response = self.fetch("/pending")
        expected_href = f"/view/station/temp/{sid}".encode()
        self.assertIn(expected_href, response.body)

    def test_temp_station_with_event_shows_at_event_name(self):
        eid = self.db.add_event(
            name="JOTA 2024",
            start_time=datetime(2024, 10, 18), end_time=datetime(2024, 10, 20),
            icon="scouts.png", color="purple", notes_template="",
            band_ids=[], mode_ids=[], url_slug="jota-2024",
        )
        self.db.add_temporary_station(
            callsign="G1EVT", club_name="Event Club",
            start_time=datetime.now(), end_time=_future(),
            latitude_degrees=51.5, longitude_degrees=-0.1,
            notes="", band_ids=[], mode_ids=[],
            event_id=eid, approved=False,
        )
        response = self.fetch("/pending")
        body = response.body.decode()
        self.assertIn("G1EVT", body)
        self.assertIn("at JOTA 2024", body)


# ---------------------------------------------------------------------------
# View station handler
# ---------------------------------------------------------------------------

class TestViewStationHandler(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        self.db = make_test_db()
        return make_app(self.db)

    def test_view_nonexistent_temp_station(self):
        response = self.fetch("/view/station/temp/99999")
        self.assertIn(b"not found", response.body.lower())

    def test_view_nonexistent_perm_station(self):
        response = self.fetch("/view/station/perm/99999")
        self.assertIn(b"not found", response.body.lower())

    def test_view_existing_temp_station(self):
        sid = self.db.add_temporary_station(
            callsign="G1VEW", club_name="View Club",
            start_time=datetime.now(), end_time=_future(),
            latitude_degrees=51.5, longitude_degrees=-0.1,
            notes="", band_ids=[], mode_ids=[],
        )
        response = self.fetch(f"/view/station/temp/{sid}")
        self.assertEqual(response.code, 200)
        self.assertIn(b"G1VEW", response.body)
        self.assertIn(b"View Club", response.body)

    def test_view_existing_perm_station(self):
        school_type_id = next(t for t in self.db.get_all_permanent_station_types() if t.name == "School").id
        sid = self.db.add_permanent_station(
            callsign="G1PVW", club_name="Perm View Club",
            latitude_degrees=51.5, longitude_degrees=-0.1,
            meeting_when="Mondays", meeting_where="Hall",
            notes="", type_id=school_type_id,
        )
        response = self.fetch(f"/view/station/perm/{sid}")
        self.assertEqual(response.code, 200)
        self.assertIn(b"G1PVW", response.body)

    def test_unapproved_station_shows_pending_notice(self):
        sid = self.db.add_temporary_station(
            callsign="G1UNA", club_name="Unapproved",
            start_time=datetime.now(), end_time=_future(),
            latitude_degrees=51.5, longitude_degrees=-0.1,
            notes="", band_ids=[], mode_ids=[],
            approved=False,
        )
        response = self.fetch(f"/view/station/temp/{sid}")
        self.assertEqual(response.code, 200)
        # Template shows an "not yet approved" alert for unapproved stations
        self.assertIn(b"not yet been approved", response.body)

    def test_approved_station_no_pending_notice(self):
        sid = self.db.add_temporary_station(
            callsign="G1APV", club_name="Approved",
            start_time=datetime.now(), end_time=_future(),
            latitude_degrees=51.5, longitude_degrees=-0.1,
            notes="", band_ids=[], mode_ids=[],
            approved=True,
        )
        response = self.fetch(f"/view/station/temp/{sid}")
        self.assertEqual(response.code, 200)
        self.assertNotIn(b"not yet been approved", response.body)


# ---------------------------------------------------------------------------
# Login handler
# ---------------------------------------------------------------------------

class TestLoginHandler(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        return make_app(make_test_db())

    def test_login_page_returns_200(self):
        response = self.fetch("/login")
        self.assertEqual(response.code, 200)

    def test_login_page_has_form(self):
        response = self.fetch("/login")
        self.assertIn(b"<form", response.body)

    def test_login_post_wrong_password_returns_401(self):
        # The login POST is AJAX-style: it returns JSON, not an HTML page.
        # Wrong credentials → 401 with a JSON error message.
        body = "username=admin&password=wrongpassword"
        response = self.fetch(
            "/login",
            method="POST",
            body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            follow_redirects=False,
        )
        self.assertEqual(response.code, 401)
        import json
        data = json.loads(response.body)
        self.assertIn("message", data)

    def test_login_post_correct_password_returns_redirect_url(self):
        # Correct credentials → 200 with JSON containing a redirect_url.
        body = "username=admin&password=password"
        response = self.fetch(
            "/login",
            method="POST",
            body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            follow_redirects=False,
        )
        self.assertEqual(response.code, 200)
        import json
        data = json.loads(response.body)
        self.assertIn("redirect_url", data)


# ---------------------------------------------------------------------------
# Admin handler (authentication required)
# ---------------------------------------------------------------------------

class TestAdminHandler(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        return make_app(make_test_db())

    def test_admin_redirects_to_login_when_unauthenticated(self):
        response = self.fetch("/admin", follow_redirects=False)
        self.assertEqual(response.code, 302)
        self.assertIn("/login", response.headers.get("Location", ""))


# ---------------------------------------------------------------------------
# Contact handler
# ---------------------------------------------------------------------------

class TestContactHandler(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        return make_app(make_test_db())

    def _post(self, body):
        return self.fetch(
            "/contact",
            method="POST",
            body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    def test_get_returns_200(self):
        response = self.fetch("/contact")
        self.assertEqual(response.code, 200)

    def test_get_contains_form(self):
        response = self.fetch("/contact")
        self.assertIn(b"<form", response.body)

    def test_get_has_name_email_message_fields(self):
        response = self.fetch("/contact")
        self.assertIn(b'name="name"', response.body)
        self.assertIn(b'name="email"', response.body)
        self.assertIn(b'name="message"', response.body)

    def test_post_with_message_returns_200(self):
        response = self._post("message=Hello+administrators")
        self.assertEqual(response.code, 200)
        import json
        data = json.loads(response.body)
        self.assertIn("message", data)

    def test_post_with_all_fields_returns_200(self):
        response = self._post("name=G1ABC&email=test%40example.com&message=Hello")
        self.assertEqual(response.code, 200)
        import json
        data = json.loads(response.body)
        self.assertIn("message", data)

    def test_post_without_message_returns_400(self):
        response = self._post("name=G1ABC&email=test%40example.com&message=")
        self.assertEqual(response.code, 400)
        import json
        data = json.loads(response.body)
        self.assertIn("message", data)

    def test_post_with_invalid_email_returns_400(self):
        response = self._post("message=Hello&email=not-an-email")
        self.assertEqual(response.code, 400)
        import json
        data = json.loads(response.body)
        self.assertIn("message", data)

    def test_post_with_html_in_message_returns_400(self):
        response = self._post("message=%3Cscript%3Ealert(1)%3C%2Fscript%3E")
        self.assertEqual(response.code, 400)
        import json
        data = json.loads(response.body)
        self.assertIn("message", data)

    def test_post_with_html_in_name_returns_400(self):
        response = self._post("name=%3Cb%3Ebold%3C%2Fb%3E&message=Hello")
        self.assertEqual(response.code, 400)
        import json
        data = json.loads(response.body)
        self.assertIn("message", data)

    def test_post_response_is_json(self):
        response = self._post("message=Hello")
        self.assertEqual(response.headers.get("Content-Type"), "application/json")

    def test_post_optional_fields_absent_succeeds(self):
        # name and email are optional — only message is required
        response = self._post("message=Just+a+message+with+no+name+or+email")
        self.assertEqual(response.code, 200)
