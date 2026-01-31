import json

from core.utils import serialize_everything
from requesthandlers.base import BaseHandler


class MapHandler(BaseHandler):
    """Handler for the main map page"""

    def get(self):
        # Get data we need to include in the template. Convert to JSON here so we can load it straight up in JS.
        temp_stations = json.dumps(self.application.db.get_all_temporary_stations(), default=serialize_everything)
        perm_stations = json.dumps(self.application.db.get_all_permanent_stations(), default=serialize_everything)

        # Render the template
        self.render("map.html", temp_stations=temp_stations, perm_stations=perm_stations)
