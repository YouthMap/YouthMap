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


def populate_derived_fields_perm_station(s):
    """Takes the provided permanent station and populates any fields in it which are derived rather than directly in the
    object as it comes out of the database. This includes icon and colour."""
    s.icon = get_icon_for_perm_station(s)
    s.color = get_color_for_perm_station(s)


def populate_derived_fields_temp_station(s):
    """Takes the provided temporary station and populates any fields in it which are derived rather than directly in the
    object as it comes out of the database. This includes icon, colour and the "humanised" time we use for display."""
    s.icon = get_icon_for_temp_station(s)
    s.color = get_color_for_temp_station(s)
    s.humanized_start_end = humanize_start_end(s.start_time, s.end_time)


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
