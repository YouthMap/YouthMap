import json

import tornado

from core.utils import populate_derived_fields_temp_station, populate_derived_fields_perm_station
from mail.mailer import notify_owner_station_approved, notify_owner_station_deleted
from requesthandlers.base import BaseHandler


class AdminApprovalHandler(BaseHandler):
    """Handler for admin approval queue page"""

    @tornado.web.authenticated
    async def get(self):
        """Get the content of the page"""

        # Get data we need to include in the template, in this case stations of either type that are not yet approved.
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

        # Render the template
        self.render("adminapproval.html", temp_stations=temp_stations, perm_stations=perm_stations)

    @tornado.web.authenticated
    async def post(self):
        """Handle the administrator clicking Approve or Delete. This supports two 'actions' depending on whether the
         Approve or Delete button was clicked. Approve sets the "approved" flag to True and Delete deletes the station."""

        executor = tornado.ioloop.IOLoop.current()
        self.set_header("Content-Type", "application/json")

        station_type = self.get_argument("type")
        station_id = int(self.get_argument("id"))

        # Get the action we have been asked to do
        action = self.get_argument("action")

        # Check for Approve action
        if action == "Approve":
            ok = False
            station = None
            if station_type == "perm":
                ok = await executor.run_in_executor(None,
                                                    lambda: self.application.db.update_permanent_station(
                                                        station_id, approved=True))
                station = await executor.run_in_executor(None,
                                                         lambda: self.application.db.get_permanent_station(
                                                             station_id))
            elif station_type == "temp":
                ok = await executor.run_in_executor(None,
                                                    lambda: self.application.db.update_temporary_station(
                                                        station_id, approved=True))
                station = await executor.run_in_executor(None,
                                                         lambda: self.application.db.get_temporary_station(
                                                             station_id))
            if ok:
                # Update OK, refresh the page and email the owner.
                self.set_status(200)
                self.write(json.dumps({"message": "Station approved.", "redirect_url": "/admin/approval"}))
                executor.run_in_executor(None, lambda: notify_owner_station_approved(self.application.db, station))
                return
            else:
                self.set_status(500)
                self.write(
                    json.dumps({"message": "Failed to update the station. Please check the logs for more details."}))
                return

        # Check for Delete action
        elif action == "Delete":
            ok = False
            station = None
            if station_type == "perm":
                station = await executor.run_in_executor(None,
                                                         lambda: self.application.db.get_permanent_station(
                                                             station_id))
                ok = await executor.run_in_executor(None,
                                                    lambda: self.application.db.delete_permanent_station(
                                                        station_id))
            elif station_type == "temp":
                station = await executor.run_in_executor(None,
                                                         lambda: self.application.db.get_temporary_station(
                                                             station_id))
                ok = await executor.run_in_executor(None,
                                                    lambda: self.application.db.delete_temporary_station(
                                                        station_id))
            if ok:
                # Update OK, refresh the page and email the owner.
                self.set_status(200)
                self.write(json.dumps({"message": "Station deleted.", "redirect_url": "/admin/approval"}))
                executor.run_in_executor(None, lambda: notify_owner_station_deleted(self.application.db, station))
                return
            else:
                self.set_status(500)
                self.write(
                    json.dumps({"message": "Failed to delete the station. Please check the logs for more details."}))
                return

        else:
            self.set_status(400)
            self.write(json.dumps({"message": "Invalid action '" + action + "'"}))
            return
