import tornado

from requesthandlers.base import BaseHandler


class AdminStationsHandler(BaseHandler):
    """Handler for admin station list page"""

    @tornado.web.authenticated
    def get(self):
        # Get data we need to include in the template
        temp_stations = self.application.db.get_all_temporary_stations()
        perm_stations = self.application.db.get_all_permanent_stations()

        # Render the template
        self.render("adminstations.html", temp_stations=temp_stations, perm_stations=perm_stations)
