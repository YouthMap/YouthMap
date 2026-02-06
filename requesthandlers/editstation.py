from core.utils import temp_station_to_json_for_user_frontend, perm_station_to_json_for_user_frontend, \
    humanize_start_end
from requesthandlers.base import BaseHandler


class EditStationHandler(BaseHandler):
    """Handler for station edit page"""

    def get(self, perm_or_temp_slug, station_id_slug):
        """Two slugs are provided here. The first is "perm" or "temp", and the second is the station ID within that
        category, so e.g. the URL can be /edit/station/temp/1 to edit permanent station 1."""

        station_id = int(station_id_slug)

        # Get data we need to include in the template
        station = None
        station_json = None
        if perm_or_temp_slug == "perm":
            station = self.application.db.get_permanent_station(station_id)
            station_json = perm_station_to_json_for_user_frontend(station)
        elif perm_or_temp_slug == "temp":
            station = self.application.db.get_temporary_station(station_id)
            station_json = temp_station_to_json_for_user_frontend(station)

        # Render the template. Supply the real object for the template and the JSON version to load more easily into
        # the map.
        self.render("editstation.html", type=perm_or_temp_slug, station=station, station_json=station_json)

    def post(self, perm_or_temp_slug, station_id_slug):
        """Handle the user filling in the form and clicking Update or Delete. This supports two 'actions' depending
        on whether the Update or Delete button was clicked. Two slugs are provided here. The first is "perm" or "temp",
        and the second is the station ID within that category, so e.g. the URL can be /edit/station/temp/1 to edit
        permanent station 1."""

        # TODO

    # TODO
