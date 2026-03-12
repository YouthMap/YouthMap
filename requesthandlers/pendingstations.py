import tornado

from core.utils import populate_derived_fields_temp_station, populate_derived_fields_perm_station
from requesthandlers.base import BaseHandler


class PendingStationsHandler(BaseHandler):
    """Handler for the public pending stations page"""

    async def get(self):
        executor = tornado.ioloop.IOLoop.current()
        all_temp = await executor.run_in_executor(None,
                                                  lambda: self.application.db.get_all_temporary_stations())
        all_perm = await executor.run_in_executor(None,
                                                  lambda: self.application.db.get_all_permanent_stations())
        temp_stations = [x for x in all_temp if not x.approved]
        perm_stations = [x for x in all_perm if not x.approved]
        for station in temp_stations:
            populate_derived_fields_temp_station(station)
        for station in perm_stations:
            populate_derived_fields_perm_station(station)

        self.render("pendingstations.html", temp_stations=temp_stations, perm_stations=perm_stations)
