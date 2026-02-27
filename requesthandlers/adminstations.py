from datetime import datetime

import tornado

from requesthandlers.base import BaseHandler


class AdminStationsHandler(BaseHandler):
    """Handler for admin station list page"""

    @tornado.web.authenticated
    async def get(self):
        # Get data we need to include in the template
        executor = tornado.ioloop.IOLoop.current()
        all_temp = await executor.run_in_executor(None,
                                                  lambda: self.application.db.get_all_temporary_stations())
        temp_stations = sorted(all_temp, key=lambda x: x.start_time)
        temp_stations_by_type = {"Past": [x for x in temp_stations if datetime.now() > x.end_time],
                                 "Current": [x for x in temp_stations if x.start_time <= datetime.now() <= x.end_time],
                                 "Future": [x for x in temp_stations if datetime.now() < x.start_time]}
        all_perm = await executor.run_in_executor(None,
                                                  lambda: self.application.db.get_all_permanent_stations())
        perm_stations = sorted(all_perm, key=lambda x: x.callsign)
        all_perm_station_types = await executor.run_in_executor(None,
                                                                lambda: self.application.db.get_all_permanent_station_types())
        perm_stations_by_type = {}
        for station_type in all_perm_station_types:
            perm_stations_by_type[station_type.name] = [x for x in perm_stations if x.type and x.type.name == station_type.name]

        # Render the template
        self.render("adminstations.html", temp_stations_by_type=temp_stations_by_type, perm_stations_by_type=perm_stations_by_type)
