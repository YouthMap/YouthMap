from requesthandlers.base import BaseHandler


class CreateStationTypeHandler(BaseHandler):
    """Handler for the interstitial page on user station creation that asks what type the station should be. Receives
    the lat/lon point the user previously picked via GET, and then passes that on along with type/event information to
    the actual 'create station' page."""

    def get(self):
        # Get data we need to include in the template
        all_events = self.application.db.get_all_events()
        all_perm_station_types = self.application.db.get_all_permanent_station_types()
        lat = self.get_argument("lat")
        lon = self.get_argument("lon")

        # Check lat/lon were supplied
        if not lat or not lon:
            self.write("Location not provided, user did not get to this page via normal means.")

        # Render the template.
        self.render("createstationtype.html", latitude_degrees=lat, longitude_degrees=lon,
                    all_perm_station_types=all_perm_station_types, all_events=all_events)

    def post(self):
        """Handle the user entering type information and clicking Next. This passes on their original lat/lon point
        information and adds in the type information that the user entered."""

        station_type = self.get_argument("station_type")
        event_id = 0
        if self.get_argument("event", None):
            event_id = int(self.get_argument("event", None))
        type_id = 0
        if self.get_argument("type", None):
            type_id = int(self.get_argument("type"))
        latitude_degrees = self.get_argument("latitude_degrees")
        longitude_degrees = self.get_argument("longitude_degrees")

        if station_type == "perm":
            self.redirect(
                "/create/station/perm?lat=" + latitude_degrees + "&lon=" + longitude_degrees + "&type=" + str(type_id))
        elif station_type == "temp":
            self.redirect("/create/station/temp?lat=" + latitude_degrees + "&lon=" + longitude_degrees + (
                ("&event=" + str(event_id)) if event_id > 0 else ""))
        else:
            self.write("Invalid station type")
