import json
from os import listdir
from os.path import isfile, join

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


def get_permanent_stations_for_user_frontend(database):
    """Get data for permanent stations, mutated to be suitable for the user frontend. This includes:
     * Removing any stations that are not approved yet
     * Removing the 'edit password' which would allow malicious editing of all stations
     * Adding icon and color
     * Replacing non-JSON-serializable objects with serializable equivalents."""

    output = []
    for s in database.get_all_permanent_stations():
        if s.approved:
            output.append({
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
            })
    print(output)
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
            output.append({
                "id": s.id,
                "callsign": s.callsign,
                "club_name": s.club_name,
                "start_time": s.start_time.isoformat(),
                "end_time": s.end_time.isoformat(),
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
            })
    print(output)
    return output


def get_events_for_user_frontend(database):
    """Get data for events, mutated to be suitable for the user frontend. This includes:
     * Removing the stations list, as the user frontend doesn't need to look up this way round
     * Replacing non-JSON-serializable objects with serializable equivalents."""

    output = []
    for e in database.get_all_events():
        if e.approved:
            output.append({
                "id": e.id,
                "name": e.name,
                "start_time": e.start_time.isoformat(),
                "end_time": e.end_time.isoformat(),
                "icon": e.icon,
                "color": e.color,
                "notes_template": e.notes_template,
                "url_slug": e.url_slug,
                "public": e.public,
                "rsgb_event": e.rsgb_event,
                "bands": [{"id": b.id, "name": b.name} for b in e.bands],
                "modes": [{"id": m.id, "name": m.name} for m in e.modes]
            })
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
