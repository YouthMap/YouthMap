import calendar
from datetime import datetime, timedelta
from os import listdir
from os.path import isfile, join

import pytz

from core.config import UPLOAD_DIR


def get_color_for_perm_station(s):
    """For a given permanent station, look up what colour it should have. This is based on its type."""
    return s.type.color


def get_icon_for_perm_station(s):
    """For a given permanent station, look up what icon it should have. This is based on its type."""
    return s.type.icon


def get_color_for_temp_station(s):
    """For a given temporary station, look up what colour it should have. This is based on its event, if it has one."""
    if s.event:
        return s.event.color
    else:
        return "red"


def get_icon_for_temp_station(s):
    """For a given temporary station, look up what icon it should have. This is based on its event, if it has one."""
    if s.event:
        return s.event.icon
    else:
        return "radio.png"


def humanize_start_end(start_time, end_time):
    """Produces a "humanised" version of the interval between two times."""
    all_day = start_time.hour == 0 and start_time.minute == 0 and end_time.hour == 23 and end_time.minute == 59
    text = ""
    if start_time.day == end_time.day and start_time.month == end_time.month and start_time.year == end_time.year:
        if not all_day:
            text += start_time.strftime("%H:%M") + " – " + end_time.strftime("%H:%M") + " UTC on "
        text += start_time.strftime("%a %-d %b %Y")
    elif start_time.month == end_time.month and start_time.year == end_time.year:
        if not all_day:
            text += start_time.strftime("%H:%M") + " UTC "
        text += start_time.strftime("%a %-d") + " – "
        if not all_day:
            text += end_time.strftime("%H:%M") + " UTC "
        text += end_time.strftime("%a %-d %b %Y")
    elif start_time.year == end_time.year:
        if not all_day:
            text += start_time.strftime("%H:%M") + " UTC "
        text += start_time.strftime("%a %-d %b") + " – "
        if not all_day:
            text += end_time.strftime("%H:%M") + " UTC "
        text += end_time.strftime("%a %-d %b %Y")
    else:
        if not all_day:
            text += start_time.strftime("%H:%M") + " UTC "
        text += start_time.strftime("%a %-d %b %Y") + " – "
        if not all_day:
            text += end_time.strftime("%H:%M") + " UTC "
        text += end_time.strftime("%a %-d %b %Y")
    return text


def perm_station_to_json_for_user_frontend(s):
    """Converts a permanent station to a JSON form suitable for sending to the frontend. This includes:
     * Removing the 'edit password' which would allow malicious editing of all stations
     * Adding icon and color
     * Replacing non-JSON-serializable objects with serializable equivalents."""

    return {
        "id": s.id,
        "callsign": s.callsign,
        "club_name": s.club_name,
        "latitude_degrees": float(s.latitude_degrees),
        "longitude_degrees": float(s.longitude_degrees),
        "meeting_when": s.meeting_when,
        "meeting_where": s.meeting_where,
        "notes": s.notes,
        "website_url": s.website_url,
        "email": s.email,
        "phone_number": s.phone_number,
        "qrz_url": s.qrz_url,
        "social_media_url": s.social_media_url,
        "type": {"id": s.type.id, "name": s.type.name},
        "icon": get_icon_for_perm_station(s),
        "color": get_color_for_perm_station(s)
    }


def temp_station_to_json_for_user_frontend(s):
    """Converts a temporary station to a JSON form suitable for sending to the frontend. This includes:
     * Removing the 'edit password' which would allow malicious editing of all stations
     * Adding icon and color
     * Replacing non-JSON-serializable objects with serializable equivalents."""

    return {
        "id": s.id,
        "callsign": s.callsign,
        "club_name": s.club_name,
        "start_time": s.start_time.isoformat(),
        "end_time": s.end_time.isoformat(),
        "humanized_start_end": humanize_start_end(s.start_time, s.end_time),
        "latitude_degrees": float(s.latitude_degrees),
        "longitude_degrees": float(s.longitude_degrees),
        "notes": s.notes,
        "website_url": s.website_url,
        "email": s.email,
        "phone_number": s.phone_number,
        "qrz_url": s.qrz_url,
        "social_media_url": s.social_media_url,
        "rsgb_attending": s.rsgb_attending,
        "event": {"id": s.event.id, "name": s.event.name} if s.event else None,
        "bands": [{"id": b.id, "name": b.name} for b in s.bands],
        "modes": [{"id": m.id, "name": m.name} for m in s.modes],
        "icon": get_icon_for_temp_station(s),
        "color": get_color_for_temp_station(s)
    }


def event_to_json_for_user_frontend(e):
    """Converts an event to a JSON form suitable for sending to the frontend. This includes:
     * Removing the stations list, as the user frontend doesn't need to look up this way round
     * Replacing non-JSON-serializable objects with serializable equivalents."""

    return {
        "id": e.id,
        "name": e.name,
        "start_time": e.start_time.isoformat(),
        "end_time": e.end_time.isoformat(),
        "humanized_start_end": humanize_start_end(e.start_time, e.end_time),
        "icon": e.icon,
        "color": e.color,
        "notes_template": e.notes_template,
        "url_slug": e.url_slug,
        "public": e.public,
        "rsgb_event": e.rsgb_event,
        "bands": [{"id": b.id, "name": b.name} for b in e.bands],
        "modes": [{"id": m.id, "name": m.name} for m in e.modes]
    }


def get_permanent_stations_for_user_frontend(database):
    """Get data for permanent stations, mutated to be suitable for the user frontend. This includes:
     * Removing any stations that are not approved yet
     * Removing the 'edit password' which would allow malicious editing of all stations
     * Adding icon and color
     * Replacing non-JSON-serializable objects with serializable equivalents."""

    output = []
    for s in database.get_all_permanent_stations():
        if s.approved:
            output.append(perm_station_to_json_for_user_frontend(s))
    return output


def get_temporary_stations_for_user_frontend(database):
    """Get data for temporary stations, mutated to be suitable for the user frontend. This includes:
     * Removing any stations that are not approved yet
     * Removing the 'edit password' which would allow malicious editing of all stations
     * Adding icon and color
     * Replacing non-JSON-serializable objects with serializable equivalents."""

    output = []
    for s in database.get_all_temporary_stations():
        if s.approved:
            output.append(temp_station_to_json_for_user_frontend(s))
    return output


def get_events_for_user_frontend(database):
    """Get data for events, mutated to be suitable for the user frontend. This includes:
     * Removing the stations list, as the user frontend doesn't need to look up this way round
     * Replacing non-JSON-serializable objects with serializable equivalents."""

    output = []
    for e in database.get_all_events():
        output.append(event_to_json_for_user_frontend(e))
    return output


def serialize_everything(obj):
    """Convert objects to serialisable things"""
    if "__dict__" in dir(obj):
        return obj.__dict__
    else:
        return None


def get_all_icons():
    """Get all icons (files in the upload directory)"""
    return sorted([f for f in listdir(UPLOAD_DIR) if isfile(join(UPLOAD_DIR, f))])


def get_default_event_start_time():
    """Returns a datetime to use as the default event/temporary station start time. This is
    implemented as 00:00 UTC on the first day of the next month."""
    return (datetime.now(pytz.UTC).replace(day=1) + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0,
                                                                                tzinfo=pytz.UTC)


def get_default_event_end_time():
    """Returns a datetime to use as the default event/temporary station end time. This is
    implemented as 23:59 UTC on the last day of the next month."""
    start = datetime.now(pytz.UTC).replace(day=1) + timedelta(days=32)
    days_in_month = calendar.monthrange(start.year, start.month)[1]
    return start.replace(day=days_in_month, hour=23, minute=59, second=59, tzinfo=pytz.UTC)
