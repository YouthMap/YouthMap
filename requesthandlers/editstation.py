from datetime import datetime

from core.utils import populate_derived_fields_temp_station, populate_derived_fields_perm_station
from requesthandlers.base import BaseHandler


class EditStationHandler(BaseHandler):
    """Handler for station edit page"""

    def get(self, perm_or_temp_slug, station_id_slug):
        """Two slugs are provided here. The first is "perm" or "temp", and the second is the station ID within that
        category, so e.g. the URL can be /edit/station/temp/1 to edit permanent station 1."""

        station_id = int(station_id_slug)

        # Get data we need to include in the template
        station = None
        if perm_or_temp_slug == "perm":
            station = self.application.db.get_permanent_station(station_id)
            populate_derived_fields_perm_station(station)
        elif perm_or_temp_slug == "temp":
            station = self.application.db.get_temporary_station(station_id)
            populate_derived_fields_temp_station(station)
        all_bands = self.application.db.get_all_bands()
        all_modes = self.application.db.get_all_modes()
        all_events = self.application.db.get_all_events()
        all_perm_station_types = self.application.db.get_all_permanent_station_types()

        # Check edit password is supplied and correct
        user_edit_password = self.get_argument("edit_password")
        edit_password_good = station.edit_password == user_edit_password
        if not edit_password_good:
            self.write("Password incorrect")
            return

        # Render the template. Supply the user password as well, this will be included in the form as a hidden field,
        # so we can check it again when it comes back to us in the POST.
        self.render("editstation.html", station_type=perm_or_temp_slug, station=station,
                    all_perm_station_types=all_perm_station_types, all_events=all_events,
                    all_bands=all_bands, all_modes=all_modes, user_edit_password=user_edit_password)

    def post(self, perm_or_temp_slug, station_id_slug):
        """Handle the user filling in the form and clicking Update or Delete. This supports two 'actions' depending
        on whether the Update or Delete button was clicked. Two slugs are provided here. The first is "perm" or "temp",
        and the second is the station ID within that category, so e.g. the URL can be /edit/station/temp/1 to edit
        permanent station 1."""

        station_id = int(station_id_slug)
        user_edit_password = self.get_argument("user_edit_password")
        edit_password_good = False

        # Check the edit password
        if perm_or_temp_slug == "perm":
            station = self.application.db.get_permanent_station(station_id)
            edit_password_good = station.edit_password == user_edit_password
        elif perm_or_temp_slug == "temp":
            station = self.application.db.get_temporary_station(station_id)
            edit_password_good = station.edit_password == user_edit_password

        if not edit_password_good:
            self.write("Password incorrect")
            return

        # Get the action we have been asked to do
        action = self.get_argument("action")

        # Check for Edit action
        if action == "Update":
            # Get request arguments. These could be for either a permanent or a temporary station at this point, so
            # get the arguments for both if they exist.
            callsign = self.get_argument("callsign")
            club_name = self.get_argument("club_name")
            event_id = 0
            if self.get_argument("event", None):
                event_id = int(self.get_argument("event", None))
            type_id = 0
            if self.get_argument("type", None):
                type_id = int(self.get_argument("type"))
            meeting_when = None
            if self.get_argument("meeting_when", None):
                meeting_when = self.get_argument("meeting_when")
            meeting_where = None
            if self.get_argument("meeting_where", None):
                meeting_where = self.get_argument("meeting_where")
            start_time = None
            if self.get_argument("start_time", None):
                start_time = datetime.strptime(self.get_argument("start_time"), "%Y-%m-%dT%H:%M")
            end_time = None
            if self.get_argument("end_time", None):
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

            # Now update the station, taking into account its type
            ok = False
            if perm_or_temp_slug == "perm":
                ok = self.application.db.update_permanent_station(station_id, callsign=callsign, club_name=club_name,
                                                                  type_id=type_id,
                                                                  latitude_degrees=latitude_degrees,
                                                                  longitude_degrees=longitude_degrees,
                                                                  meeting_when=meeting_when,
                                                                  meeting_where=meeting_where,
                                                                  notes=notes, website_url=website_url, qrz_url=qrz_url,
                                                                  social_media_url=social_media_url, email=email,
                                                                  phone_number=phone_number)
            elif perm_or_temp_slug == "temp":
                ok = self.application.db.update_temporary_station(station_id, callsign=callsign, club_name=club_name,
                                                                  event_id=event_id, start_time=start_time,
                                                                  end_time=end_time,
                                                                  latitude_degrees=latitude_degrees,
                                                                  longitude_degrees=longitude_degrees,
                                                                  band_ids=band_ids,
                                                                  mode_ids=mode_ids,
                                                                  notes=notes, website_url=website_url, qrz_url=qrz_url,
                                                                  social_media_url=social_media_url, email=email,
                                                                  phone_number=phone_number)

            if ok:
                # Update OK, go back to the view station page to show new data
                self.redirect("/view/station/" + perm_or_temp_slug + "/" + station_id_slug)
            else:
                self.write("Failed to update station")
                return

        # Check for Delete action
        elif action == "Delete":
            if perm_or_temp_slug == "perm":
                self.application.db.delete_permanent_station(station_id)
            elif perm_or_temp_slug == "temp":
                self.application.db.delete_temporary_station(station_id)
            self.redirect("/")

        else:
            self.write("Invalid action '" + action + "'")