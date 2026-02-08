from core.utils import populate_derived_fields_temp_station, populate_derived_fields_perm_station
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
        self.render("createstationtype.html", latitude_degrees=lat, longitude_degrees=lon, all_perm_station_types=all_perm_station_types, all_events=all_events)

    def post(self):
        """Handle the user entering type information and clicking Next. This passes on their original lat/lon point
        information and adds in the type information that the user entered."""

        TODO
