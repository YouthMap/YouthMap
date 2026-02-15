import tornado

from core.utils import populate_derived_fields_temp_station, populate_derived_fields_perm_station
from requesthandlers.base import BaseHandler


# noinspection PyUnresolvedReferences
class AdminApprovalHandler(BaseHandler):
    """Handler for admin approval queue page"""

    @tornado.web.authenticated
    def get(self):
        # Get data we need to include in the template, in this case stations of either type that are not yet approved.
        temp_stations = [x for x in self.application.db.get_all_temporary_stations() if not x.approved]
        perm_stations = [x for x in self.application.db.get_all_permanent_stations() if not x.approved]
        for station in temp_stations:
            populate_derived_fields_temp_station(station)
        for station in perm_stations:
            populate_derived_fields_perm_station(station)

        # Render the template
        self.render("adminapproval.html", temp_stations=temp_stations, perm_stations=perm_stations)

    @tornado.web.authenticated
    def post(self):
        # TODO
        pass
