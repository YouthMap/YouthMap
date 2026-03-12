"""Tests for database/operations.py — uses an in-memory SQLite database."""

from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _future():
    """Return a datetime one year from now."""
    return datetime.now() + timedelta(days=365)


def _past():
    """Return a datetime one year in the past."""
    return datetime.now() - timedelta(days=365)


def add_temp_station(db, callsign="G1TST", club_name="Test Club", approved=False, event_id=None):
    """Helper to insert a minimal temporary station and return its ID."""
    return db.add_temporary_station(
        callsign=callsign,
        club_name=club_name,
        start_time=datetime.now(),
        end_time=_future(),
        latitude_degrees=51.5,
        longitude_degrees=-0.1,
        notes="",
        band_ids=[],
        mode_ids=[],
        event_id=event_id,
        approved=approved,
    )


def add_perm_station(db, callsign="G1PRM", club_name="Perm Club", approved=False):
    """Helper to insert a minimal permanent station and return its ID."""
    return db.add_permanent_station(
        callsign=callsign,
        club_name=club_name,
        latitude_degrees=51.5,
        longitude_degrees=-0.1,
        meeting_when="Mondays",
        meeting_where="The clubhouse",
        notes="",
        approved=approved,
    )


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class TestConfig:
    def test_config_exists_after_init(self, db):
        config = db.get_config()
        assert config is not None

    def test_config_defaults(self, db):
        config = db.get_config()
        assert config.enable_mail is False
        assert config.enable_captcha is False

    def test_update_config(self, db):
        ok = db.update_config(base_url="https://example.com")
        assert ok is True
        config = db.get_config()
        assert config.base_url == "https://example.com"

    def test_update_config_partial(self, db):
        db.update_config(base_url="https://before.com")
        db.update_config(enable_captcha=True)
        config = db.get_config()
        # base_url should be unchanged
        assert config.base_url == "https://before.com"
        assert config.enable_captcha is True


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class TestUsers:
    def test_default_admin_user_exists(self, db):
        users = db.get_all_users()
        assert any(u.username == "admin" for u in users)

    def test_add_user_returns_id(self, db):
        uid = db.add_user("testuser", "password123", "test@example.com", False)
        assert uid is not None

    def test_get_user_by_id(self, db):
        uid = db.add_user("testuser", "password123", "test@example.com", False)
        user = db.get_user(uid)
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.super_admin is False

    def test_get_nonexistent_user_returns_none(self, db):
        assert db.get_user(99999) is None

    def test_verify_user_correct_password(self, db):
        uid = db.add_user("alice", "s3cr3t", "alice@example.com", False)
        result = db.verify_user("alice", "s3cr3t")
        assert result == uid

    def test_verify_user_wrong_password(self, db):
        db.add_user("bob", "correct", "bob@example.com", False)
        result = db.verify_user("bob", "wrong")
        assert result is None

    def test_verify_user_case_insensitive_username(self, db):
        uid = db.add_user("Charlie", "pw", "charlie@example.com", False)
        result = db.verify_user("charlie", "pw")
        assert result == uid

    def test_update_user_email(self, db):
        uid = db.add_user("dave", "pw", "old@example.com", False)
        db.update_user(uid, email="new@example.com")
        user = db.get_user(uid)
        assert user.email == "new@example.com"

    def test_update_user_password(self, db):
        uid = db.add_user("eve", "old_pw", "eve@example.com", False)
        db.update_user(uid, password="new_pw")
        assert db.verify_user("eve", "new_pw") == uid
        assert db.verify_user("eve", "old_pw") is None

    def test_delete_user(self, db):
        uid = db.add_user("frank", "pw", "frank@example.com", False)
        ok = db.delete_user(uid)
        assert ok is True
        assert db.get_user(uid) is None

    def test_delete_nonexistent_user(self, db):
        assert db.delete_user(99999) is False

    def test_is_insecure_user_present_with_default(self, db):
        # The default admin:password user is created on init
        assert db.is_insecure_user_present() is True

    def test_is_insecure_user_not_present_after_password_change(self, db):
        admin_id = db.verify_user("admin", "password")
        db.update_user(admin_id, password="S3cur3P@ss!")
        assert db.is_insecure_user_present() is False


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

class TestSessions:
    def test_create_and_verify_session(self, db):
        uid = db.add_user("grace", "pw", "g@example.com", False)
        token = db.create_user_session(uid)
        assert token is not None
        result = db.verify_user_session_token(token)
        assert result == uid

    def test_nonexistent_token_rejected(self, db):
        result = db.verify_user_session_token("notarealtoken")
        assert result is None

    def test_cleanup_expired_sessions(self, db):
        # Create a session, then forcibly expire it by manipulating the DB directly
        uid = db.add_user("henry", "pw", "h@example.com", False)
        token = db.create_user_session(uid)

        # Expire the session using a direct SQLAlchemy update
        from database.models import UserSession
        session = db.SessionLocal()
        try:
            user_session = session.query(UserSession).filter_by(session_token=token).first()
            user_session.expires_at = datetime.now() - timedelta(hours=1)
            session.commit()
        finally:
            session.close()

        ok = db.cleanup_expired_sessions()
        assert ok is True
        assert db.verify_user_session_token(token) is None


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

class TestEvents:
    def test_add_event_returns_id(self, db):
        eid = db.add_event(
            name="JOTA 2024",
            start_time=datetime(2024, 10, 18),
            end_time=datetime(2024, 10, 20),
            icon="scouts.png",
            color="purple",
            notes_template="",
            band_ids=[],
            mode_ids=[],
            url_slug="jota-2024",
        )
        assert eid is not None

    def test_get_event(self, db):
        eid = db.add_event(
            name="Field Day 2024",
            start_time=datetime(2024, 6, 1),
            end_time=datetime(2024, 6, 2),
            icon="radio.png",
            color="blue",
            notes_template="",
            band_ids=[],
            mode_ids=[],
            url_slug="field-day-2024",
        )
        event = db.get_event(eid)
        assert event.name == "Field Day 2024"
        assert event.color == "blue"
        assert event.url_slug == "field-day-2024"

    def test_get_nonexistent_event(self, db):
        assert db.get_event(99999) is None

    def test_get_all_events(self, db):
        initial = len(db.get_all_events())
        db.add_event("Ev1", datetime(2025, 1, 1), datetime(2025, 1, 2), "i.png", "red", "", [], [], "ev1")
        db.add_event("Ev2", datetime(2025, 2, 1), datetime(2025, 2, 2), "i.png", "red", "", [], [], "ev2")
        assert len(db.get_all_events()) == initial + 2

    def test_update_event(self, db):
        eid = db.add_event("Ev", datetime(2025, 1, 1), datetime(2025, 1, 2), "i.png", "red", "", [], [], "ev")
        ok = db.update_event(eid, name="Updated Event", color="green")
        assert ok is True
        event = db.get_event(eid)
        assert event.name == "Updated Event"
        assert event.color == "green"

    def test_delete_event(self, db):
        eid = db.add_event("Del", datetime(2025, 1, 1), datetime(2025, 1, 2), "i.png", "red", "", [], [], "del")
        ok = db.delete_event(eid)
        assert ok is True
        assert db.get_event(eid) is None

    def test_delete_event_cascades_to_temp_stations(self, db):
        eid = db.add_event("Cascade", datetime(2025, 1, 1), datetime(2025, 1, 2), "i.png", "red", "", [], [], "cascade")
        sid = add_temp_station(db, event_id=eid)
        db.delete_event(eid)
        assert db.get_temporary_station(sid) is None


# ---------------------------------------------------------------------------
# Temporary Stations
# ---------------------------------------------------------------------------

class TestTemporaryStations:
    def test_add_returns_id(self, db):
        sid = add_temp_station(db)
        assert sid is not None

    def test_get_station(self, db):
        sid = add_temp_station(db, callsign="G1TST", club_name="My Club")
        station = db.get_temporary_station(sid)
        assert station.callsign == "G1TST"
        assert station.club_name == "My Club"
        assert station.approved is False

    def test_get_nonexistent_station(self, db):
        assert db.get_temporary_station(99999) is None

    def test_edit_password_auto_generated(self, db):
        sid = add_temp_station(db)
        station = db.get_temporary_station(sid)
        assert station.edit_password is not None
        assert len(station.edit_password) == 10

    def test_get_all_returns_all(self, db):
        initial = len(db.get_all_temporary_stations())
        add_temp_station(db, callsign="G1AAA")
        add_temp_station(db, callsign="G1BBB")
        assert len(db.get_all_temporary_stations()) == initial + 2

    def test_update_callsign(self, db):
        sid = add_temp_station(db, callsign="G1OLD")
        ok = db.update_temporary_station(sid, callsign="G1NEW")
        assert ok is True
        assert db.get_temporary_station(sid).callsign == "G1NEW"

    def test_approve_station(self, db):
        sid = add_temp_station(db, approved=False)
        db.update_temporary_station(sid, approved=True)
        assert db.get_temporary_station(sid).approved is True

    def test_update_nonexistent_station(self, db):
        assert db.update_temporary_station(99999, callsign="X") is False

    def test_delete_station(self, db):
        sid = add_temp_station(db)
        ok = db.delete_temporary_station(sid)
        assert ok is True
        assert db.get_temporary_station(sid) is None

    def test_delete_nonexistent_station(self, db):
        assert db.delete_temporary_station(99999) is False

    def test_get_by_event(self, db):
        eid = db.add_event("Ev", datetime(2025, 1, 1), datetime(2025, 1, 2), "i.png", "red", "", [], [], "ev-slug")
        sid1 = add_temp_station(db, callsign="G1EVT", event_id=eid)
        add_temp_station(db, callsign="G1NOE")
        stations = db.get_temporary_stations_by_event(eid)
        ids = [s.id for s in stations]
        assert sid1 in ids
        assert all(s.event_id == eid for s in stations)

    def test_station_with_bands_and_modes(self, db):
        bands = db.get_all_bands()
        modes = db.get_all_modes()
        band_ids = [b.id for b in bands[:2]]
        mode_ids = [m.id for m in modes[:1]]
        sid = db.add_temporary_station(
            callsign="G1BND", club_name="Band Club",
            start_time=datetime.now(), end_time=_future(),
            latitude_degrees=51.0, longitude_degrees=0.0,
            notes="", band_ids=band_ids, mode_ids=mode_ids,
        )
        station = db.get_temporary_station(sid)
        assert len(station.bands) == 2
        assert len(station.modes) == 1


# ---------------------------------------------------------------------------
# Permanent Stations
# ---------------------------------------------------------------------------

class TestPermanentStations:
    def test_add_returns_id(self, db):
        sid = add_perm_station(db)
        assert sid is not None

    def test_get_station(self, db):
        sid = add_perm_station(db, callsign="G1PRM", club_name="Perm Club")
        station = db.get_permanent_station(sid)
        assert station.callsign == "G1PRM"
        assert station.club_name == "Perm Club"
        assert station.approved is False

    def test_get_nonexistent_station(self, db):
        assert db.get_permanent_station(99999) is None

    def test_edit_password_auto_generated(self, db):
        sid = add_perm_station(db)
        station = db.get_permanent_station(sid)
        assert station.edit_password is not None
        assert len(station.edit_password) == 10

    def test_get_all_returns_all(self, db):
        initial = len(db.get_all_permanent_stations())
        add_perm_station(db, callsign="G1AAA")
        add_perm_station(db, callsign="G1BBB")
        assert len(db.get_all_permanent_stations()) == initial + 2

    def test_update_callsign(self, db):
        sid = add_perm_station(db, callsign="G1OLD")
        ok = db.update_permanent_station(sid, callsign="G1NEW")
        assert ok is True
        assert db.get_permanent_station(sid).callsign == "G1NEW"

    def test_approve_station(self, db):
        sid = add_perm_station(db, approved=False)
        db.update_permanent_station(sid, approved=True)
        assert db.get_permanent_station(sid).approved is True

    def test_update_nonexistent_station(self, db):
        assert db.update_permanent_station(99999, callsign="X") is False

    def test_delete_station(self, db):
        sid = add_perm_station(db)
        ok = db.delete_permanent_station(sid)
        assert ok is True
        assert db.get_permanent_station(sid) is None

    def test_delete_nonexistent_station(self, db):
        assert db.delete_permanent_station(99999) is False

    def test_get_by_type(self, db):
        types = db.get_all_permanent_station_types()
        school_type = next(t for t in types if t.name == "School")
        sid = add_perm_station(db, callsign="G1SCH")
        db.update_permanent_station(sid, type_id=school_type.id)
        stations = db.get_permanent_stations_by_type(school_type.id)
        assert any(s.id == sid for s in stations)


# ---------------------------------------------------------------------------
# Reference data (bands, modes, permanent station types)
# ---------------------------------------------------------------------------

class TestReferenceData:
    def test_bands_populated(self, db):
        bands = db.get_all_bands()
        names = [b.name for b in bands]
        assert "2m" in names
        assert "70cm" in names
        assert "20m" in names

    def test_modes_populated(self, db):
        modes = db.get_all_modes()
        names = [m.name for m in modes]
        assert "CW" in names
        assert "Phone" in names
        assert "Data" in names

    def test_permanent_station_types_populated(self, db):
        types = db.get_all_permanent_station_types()
        names = [t.name for t in types]
        assert "School" in names
        assert "University" in names
        assert "Cadet" in names
