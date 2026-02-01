import json

from core.utils import get_permanent_stations_for_user_frontend, \
    get_temporary_stations_for_user_frontend
from requesthandlers.base import BaseHandler


class MapHandler(BaseHandler):
    """Handler for the main map page"""

    def get(self):
        # Get data we need to include in the template. Convert to JSON here so we can load it straight up in JS.
        temp_stations = json.dumps(get_permanent_stations_for_user_frontend(self.application.db))
        perm_stations = json.dumps(get_temporary_stations_for_user_frontend(self.application.db))

        # Render the template
        self.render("map.html", temp_stations=temp_stations, perm_stations=perm_stations)
