import csv
from io import StringIO

import tornado

from requesthandlers.base import BaseHandler


class AdminExportHandler(BaseHandler):
    """Handler for admin export page, and the export capability itself. If no GET params are supplied, the page is
    rendered. If params are supplied, a CSV output is returned with the export data in it. So you can GET /admin/export
    and it will return the HTML menu page, but GET /admin/export?data=stations will get you a CSV of all station data."""

    @tornado.web.authenticated
    def get(self):
        # Deny access if we are not a super-admin
        user = self.application.db.get_user(self.current_user)
        if not user.super_admin:
            self.write("You do not have permission to access this page.")
            return

        # Figure out if we have no GET params (in which case this is a request for the HTML page itself) or if we have
        # them, in which case this is a request for data
        data = self.get_argument("data", None)

        if not data:
            # Return the HTML
            events = sorted(self.application.db.get_all_events(), key=lambda x: x.start_time)
            self.render("adminexport.html", events=events)

        elif data == "stations":
            self.set_status(200)
            self.set_header("Content-Type", "text/csv")

            event_id = self.get_argument("event", None)
            if event_id:
                self.write(self.get_csv_for_event_stations(event_id))
            else:
                self.write(self.get_csv_for_all_stations())

        elif data == "events":
            self.set_status(200)
            self.set_header("Content-Type", "text/csv")

            self.write(self.get_csv_for_all_events())

        else:
            self.set_status(400)
            self.write("Invalid data value '" + data + "'")
            return

    def get_csv_for_event_stations(self, event_id):
        """Returns CSV content listing temporary stations that have the provided event."""

        event_stations = sorted(self.application.db.get_temporary_stations_by_event(event_id), key=lambda x: x.id)
        fieldnames = [
            'id',
            'callsign',
            'club_name',
            'event_id',
            'event_name',
            'start_time',
            'end_time',
            'latitude_degrees',
            'longitude_degrees',
            'notes',
            'website_url',
            'email',
            'phone_number',
            'qrz_url',
            'social_media_url',
            'rsgb_attending',
            'approved',
            'bands',
            'modes',
        ]

        # Open a StringIO object to write to and write a header
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        # Iterate through temporary stations, writing each line
        for station in event_stations:
            writer.writerow({
                'id': station.id,
                'callsign': station.callsign,
                'club_name': station.club_name,
                'event_id': station.event_id if station.event_id else '',
                'event_name': station.event.name if station.event else '',
                'start_time': station.start_time.isoformat(),
                'end_time': station.end_time.isoformat(),
                'latitude_degrees': station.latitude_degrees,
                'longitude_degrees': station.longitude_degrees,
                'notes': station.notes if station.notes else '',
                'website_url': station.website_url if station.website_url else '',
                'email': station.email if station.email else '',
                'phone_number': station.phone_number if station.phone_number else '',
                'qrz_url': station.qrz_url if station.qrz_url else '',
                'social_media_url': station.social_media_url if station.social_media_url else '',
                'rsgb_attending': station.rsgb_attending,
                'approved': station.approved,
                'bands': ', '.join([band.name for band in station.bands]) if station.bands else '',
                'modes': ', '.join([mode.name for mode in station.modes]) if station.modes else '',
            })

        # Get the CSV string and return it
        csv_string = output.getvalue()
        output.close()
        return csv_string

    def get_csv_for_all_stations(self):
        """Returns CSV content listing all stations, both temporary and permanent."""

        permanent_stations = sorted(self.application.db.get_all_permanent_stations(), key=lambda x: x.id)
        temporary_stations = sorted(self.application.db.get_all_temporary_stations(), key=lambda x: x.id)

        # Define the superset of all fields from both station types
        fieldnames = [
            # Common fields
            'station_type',
            'id',
            'callsign',
            'club_name',
            'latitude_degrees',
            'longitude_degrees',
            'approved',
            'notes',
            'website_url',
            'email',
            'phone_number',
            'qrz_url',
            'social_media_url',
            # Temporary station only fields
            'event_id',
            'event_name',
            'start_time',
            'end_time',
            'rsgb_attending',
            'bands',
            'modes',
            # Permanent station only fields
            'type_id',
            'type_name',
            'meeting_when',
            'meeting_where'
        ]

        # Open a StringIO object to write to and write a header
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        # Iterate through all stations, writing each line
        for station in temporary_stations:
            writer.writerow({
                'station_type': 'temporary',
                'id': station.id,
                'callsign': station.callsign,
                'club_name': station.club_name,
                'latitude_degrees': station.latitude_degrees,
                'longitude_degrees': station.longitude_degrees,
                'approved': station.approved,
                'event_id': station.event_id if station.event_id else '',
                'event_name': station.event.name if station.event else '',
                'start_time': station.start_time.isoformat(),
                'end_time': station.end_time.isoformat(),
                'rsgb_attending': station.rsgb_attending,
                'bands': ', '.join([band.name for band in station.bands]) if station.bands else '',
                'modes': ', '.join([mode.name for mode in station.modes]) if station.modes else '',
                'notes': station.notes if station.notes else '',
                'website_url': station.website_url if station.website_url else '',
                'email': station.email if station.email else '',
                'phone_number': station.phone_number if station.phone_number else '',
                'qrz_url': station.qrz_url if station.qrz_url else '',
                'social_media_url': station.social_media_url if station.social_media_url else '',
            })
        for station in permanent_stations:
            writer.writerow({
                'station_type': 'permanent',
                'id': station.id,
                'callsign': station.callsign,
                'club_name': station.club_name,
                'latitude_degrees': station.latitude_degrees,
                'longitude_degrees': station.longitude_degrees,
                'approved': station.approved,
                'type_id': station.type_id if station.type_id else '',
                'type_name': station.type.name if station.type else '',
                'meeting_when': station.meeting_when,
                'meeting_where': station.meeting_where,
                'notes': station.notes if station.notes else '',
                'website_url': station.website_url if station.website_url else '',
                'email': station.email if station.email else '',
                'phone_number': station.phone_number if station.phone_number else '',
                'qrz_url': station.qrz_url if station.qrz_url else '',
                'social_media_url': station.social_media_url if station.social_media_url else '',
            })

        # Get the CSV string and return it
        csv_string = output.getvalue()
        output.close()
        return csv_string

    def get_csv_for_all_events(self):
        """Creates a CSV table of all events and returns it as a string."""

        events = sorted(self.application.db.get_all_events(), key=lambda x: x.id)
        fieldnames = [
            'id',
            'name',
            'start_time',
            'end_time',
            'icon',
            'color',
            'notes_template',
            'url_slug',
            'public',
            'rsgb_event',
            'bands',
            'modes',
        ]

        # Open a StringIO object to write to and write a header
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        # Iterate through events, writing each line
        for event in events:
            writer.writerow({
                'id': event.id,
                'name': event.name,
                'start_time': event.start_time.isoformat(),
                'end_time': event.end_time.isoformat(),
                'icon': event.icon,
                'color': event.color,
                'notes_template': event.notes_template,
                'url_slug': event.url_slug,
                'public': event.public,
                'rsgb_event': event.rsgb_event,
                'bands': ', '.join([band.name for band in event.bands]) if event.bands else '',
                'modes': ', '.join([mode.name for mode in event.modes]) if event.modes else '',
            })

        # Get the CSV string and return it
        csv_string = output.getvalue()
        output.close()
        return csv_string
