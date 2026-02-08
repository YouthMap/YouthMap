from datetime import datetime

from core.utils import TEMP_STATION_NO_EVENT_COLOR, TEMP_STATION_NO_EVENT_ICON, get_default_event_start_time, \
    get_default_event_end_time
from requesthandlers.base import BaseHandler


class CreateStationHandler(BaseHandler):
    """Handler for the create station page (the full version where the user fills in the form, rather than the
    interstitial page where they set the type"""

    def get(self, perm_or_temp_slug):
        """A slug is provided here, "perm" or "temp", depending on the type of station we want to create, which sets
        what's included in the form template. The form of the URL is /create/station/temp or /create/station/perm."""

        # Get data we need to include in the template. This is the list of bands and modes in case we are creating
        # a temporary station and need to set these, event and type IDs, and default start and end times for the event.
        all_bands = self.application.db.get_all_bands()
        all_modes = self.application.db.get_all_modes()
        default_start = get_default_event_start_time()
        default_end = get_default_event_end_time()
        lat = self.get_argument("lat")
        lon = self.get_argument("lon")
        event_id = 0
        if self.get_argument("event", None):
            event_id = int(self.get_argument("event", None))
        type_id = 0
        if self.get_argument("type", None):
            type_id = int(self.get_argument("type"))

        # Check lat/lon were supplied
        if not lat or not lon or (event_id == 0 and type_id == 0):
            self.write("Required parameters not provided, user did not get to this page via normal means.")

        # Derive color/icon. We have to do this manually because we don't have a real station object yet, but for a nice
        # display for the user we want to use the real marker icon and colour at this point.
        type = None
        event = None
        color = TEMP_STATION_NO_EVENT_COLOR
        icon = TEMP_STATION_NO_EVENT_ICON
        if perm_or_temp_slug == "perm":
            type = self.application.db.get_permanent_station_type(type_id)
            color = type.color
            icon = type.icon
        elif perm_or_temp_slug == "temp":
            event = self.application.db.get_event(event_id)
            if event:
                color = event.color
                icon = event.icon


        # Render the template. Supply the user password as well, this will be included in the form as a hidden field,
        # so we can check it again when it comes back to us in the POST.
        self.render("createstation.html", station_type=perm_or_temp_slug, latitude_degrees=lat, longitude_degrees=lon,
                    event=event, event_id=event_id, type=type, type_id=type_id, color=color, icon=icon,
                    all_bands=all_bands, all_modes=all_modes, default_start=default_start, default_end=default_end)

    def post(self, perm_or_temp_slug):
        """Handle the user filling in the form and clicking Create. The "perm" or "temp" slug is provided here as well."""

        # Get the action we have been asked to do
        action = self.get_argument("action")

        # Check for Create action
        if action == "Create":
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

            # Now create the station, taking into account its type
            new_station_id = None
            if perm_or_temp_slug == "perm":
                new_station_id = self.application.db.add_permanent_station(callsign=callsign, club_name=club_name,
                                                                           type_id=type_id,
                                                                           latitude_degrees=latitude_degrees,
                                                                           longitude_degrees=longitude_degrees,
                                                                           meeting_when=meeting_when,
                                                                           meeting_where=meeting_where,
                                                                           notes=notes, website_url=website_url,
                                                                           qrz_url=qrz_url,
                                                                           social_media_url=social_media_url,
                                                                           email=email,
                                                                           phone_number=phone_number)
            elif perm_or_temp_slug == "temp":
                new_station_id = self.application.db.add_temporary_station(callsign=callsign, club_name=club_name,
                                                                              event_id=event_id, start_time=start_time,
                                                                              end_time=end_time,
                                                                              latitude_degrees=latitude_degrees,
                                                                              longitude_degrees=longitude_degrees,
                                                                              band_ids=band_ids,
                                                                              mode_ids=mode_ids,
                                                                              notes=notes, website_url=website_url,
                                                                              qrz_url=qrz_url,
                                                                              social_media_url=social_media_url,
                                                                              email=email,
                                                                              phone_number=phone_number)

            if new_station_id:
                # Create OK, go back to the view station page to show the data
                # TODO we need to show the edit password here in a modal or something
                self.redirect("/view/station/" + perm_or_temp_slug + "/" + str(new_station_id))
            else:
                self.write("Failed to create station")
                return

        else:
            self.write("Unknown action")
