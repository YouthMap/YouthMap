from requesthandlers.base import BaseHandler


class MapHandler(BaseHandler):
    """Handler for the main map page"""

    def get(self):
        # Get values we need to include in the template

        # Render the template
        self.render("map.html")
