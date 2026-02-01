from datetime import datetime

import tornado

from core.utils import get_default_event_end_time, get_default_event_start_time
from requesthandlers.base import BaseHandler


class AdminStationTempHandler(BaseHandler):
    """Handler for admin temporary station editing page"""

    @tornado.web.authenticated
    def get(self, slug):
        """The slug here is the temporary station ID, so e.g. the URL can be /admin/station/temp/1 to edit temporary
        station 1. A special slug of 'new' is also allowed, which sets up the form to create a temporary station rather
        than to edit one."""

        station_id = int(slug) if slug != "new" else None
        creating_new = (slug == "new")

        # Get data we need to include in the template
        station = self.application.db.get_temporary_station(station_id) if not creating_new else None
        all_bands = self.application.db.get_all_bands()
        all_modes = self.application.db.get_all_modes()
        all_events = self.application.db.get_all_events()
        default_start = get_default_event_start_time()
        default_end = get_default_event_end_time()

        # Render the template
        self.render("adminstationtemp.html", station=station, creating_new=creating_new, all_events=all_events,
                    all_bands=all_bands, all_modes=all_modes, default_start=default_start, default_end=default_end)

    @tornado.web.authenticated
    def post(self, slug):
        """Handles POST requests for temporary station editing page. This supports three 'actions' depending on whether
        the Update or Delete button was clicked for an existing station, or the Create button was clicked for a new
        station, and provides the updated data to insert back into the database. The slug here is the temporary station
        ID, so e.g. the URL can be /admin/station/temp/1 to edit temporary station 1. A special slug of 'new' is also
        allowed, which sets up the form to create a temporary station rather than to edit one."""

        station_id = int(slug) if slug != "new" else None

        # Get the action we have been asked to do
        action = self.get_argument("action")

        # Check for Delete action
        if action == "Delete":
            # Process the delete action
            ok = self.application.db.delete_temporary_station(station_id)
            if ok:
                # Delete OK, go back to stations list
                self.redirect("/admin/stations")
            else:
                self.write("Failed to delete station")

        # Check for Update action
        elif action == "Update":
            # Get request arguments
            callsign = self.get_argument("callsign")
            club_name = self.get_argument("club_name")
            event_id = 0
            if self.get_argument("event", None):
                event_id = self.get_argument("event", None)
            start_time = datetime.strptime(self.get_argument("start_time"), "%Y-%m-%dT%H:%M")
            end_time = datetime.strptime(self.get_argument("end_time"), "%Y-%m-%dT%H:%M")
            latitude_degrees = float(self.get_argument("latitude_degrees"))
            longitude_degrees = float(self.get_argument("longitude_degrees"))
            band_ids = []
            if self.get_argument("bands[]", None):
                band_ids = [int(x) for x in self.request.arguments["bands[]"]]
            mode_ids = []
            if self.get_argument("modes[]", None):
                mode_ids = [int(x) for x in self.request.arguments["modes[]"]]
            notes = self.get_argument("notes", None)
            notes = notes if notes else ""
            website_url = self.get_argument("website_url", None)
            website_url = website_url if website_url else ""
            qrz_url = self.get_argument("qrz_url", None)
            qrz_url = qrz_url if qrz_url else ""
            social_media_url = self.get_argument("social_media_url", None)
            social_media_url = social_media_url if social_media_url else ""
            email = self.get_argument("email", None)
            email = email if email else ""
            phone_number = self.get_argument("phone_number", None)
            phone_number = phone_number if phone_number else ""
            rsgb_attending = True if self.get_argument("rsgb_attending", None) else False
            approved = True if self.get_argument("approved", None) else False
            edit_password = self.get_argument("edit_password")

            # Process the update
            ok = self.application.db.update_temporary_station(station_id, callsign=callsign, club_name=club_name,
                                                              event_id=event_id, start_time=start_time,
                                                              end_time=end_time,
                                                              latitude_degrees=latitude_degrees,
                                                              longitude_degrees=longitude_degrees, band_ids=band_ids,
                                                              mode_ids=mode_ids,
                                                              notes=notes, website_url=website_url, qrz_url=qrz_url,
                                                              social_media_url=social_media_url, email=email,
                                                              phone_number=phone_number, rsgb_attending=rsgb_attending,
                                                              approved=approved,
                                                              edit_password=edit_password)
            if ok:
                # Update OK, just reload the page which will have the new data in it
                self.redirect("/admin/station/temp/" + slug)
            else:
                self.write("Failed to update station")
                return

        # Check for Create action
        elif action == "Create":
            # Get request arguments.
            callsign = self.get_argument("callsign")
            club_name = self.get_argument("club_name")
            event_id = 0
            if self.get_argument("event", None):
                event_id = self.get_argument("event", None)
            start_time = datetime.strptime(self.get_argument("start_time"), "%Y-%m-%dT%H:%M")
            end_time = datetime.strptime(self.get_argument("end_time"), "%Y-%m-%dT%H:%M")
            latitude_degrees = float(self.get_argument("latitude_degrees"))
            longitude_degrees = float(self.get_argument("longitude_degrees"))
            band_ids = []
            if self.get_argument("bands[]", None):
                band_ids = [int(x) for x in self.request.arguments["bands[]"]]
            mode_ids = []
            if self.get_argument("modes[]", None):
                mode_ids = [int(x) for x in self.request.arguments["modes[]"]]
            notes = self.get_argument("notes", None)
            notes = notes if notes else ""
            website_url = self.get_argument("website_url", None)
            website_url = website_url if website_url else ""
            qrz_url = self.get_argument("qrz_url", None)
            qrz_url = qrz_url if qrz_url else ""
            social_media_url = self.get_argument("social_media_url", None)
            social_media_url = social_media_url if social_media_url else ""
            email = self.get_argument("email", None)
            email = email if email else ""
            phone_number = self.get_argument("phone_number", None)
            phone_number = phone_number if phone_number else ""
            rsgb_attending = True if self.get_argument("rsgb_attending", None) else False
            approved = True if self.get_argument("approved", None) else False

            # Process the create action
            new_station_id = self.application.db.add_temporary_station(callsign=callsign, club_name=club_name,
                                                                       event_id=event_id, start_time=start_time,
                                                                       end_time=end_time,
                                                                       latitude_degrees=latitude_degrees,
                                                                       longitude_degrees=longitude_degrees,
                                                                       band_ids=band_ids,
                                                                       mode_ids=mode_ids,
                                                                       notes=notes, website_url=website_url,
                                                                       qrz_url=qrz_url,
                                                                       social_media_url=social_media_url, email=email,
                                                                       phone_number=phone_number,
                                                                       rsgb_attending=rsgb_attending,
                                                                       approved=approved)
            if new_station_id:
                # Create OK, just reload the page which will have the new data in it
                self.redirect("/admin/station/temp/" + str(new_station_id))
            else:
                self.write("Failed to update station")
                return

        else:
            self.write("Invalid action '" + action + "'")
