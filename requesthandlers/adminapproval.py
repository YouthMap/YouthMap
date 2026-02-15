import json
import tornado

from core.utils import populate_derived_fields_temp_station, populate_derived_fields_perm_station
from requesthandlers.base import BaseHandler


# noinspection PyUnresolvedReferences
class AdminApprovalHandler(BaseHandler):
    """Handler for admin approval queue page"""

    @tornado.web.authenticated
    def get(self):
        """Get the content of the page"""

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
        """Handle the administrator clicking Approve or Deny. This supports two 'actions' depending on whether the
         Approve or Deny button was clicked. Approve sets the "approved" flag to True and Deny deletes the station."""

        self.set_header("Content-Type", "application/json")

        station_type = self.get_argument("type")
        station_id = int(self.get_argument("id"))

        # Get the action we have been asked to do
        action = self.get_argument("action")

        # Check for Approve action
        if action == "Approve":
            ok = False
            if station_type == "perm":
                ok = self.application.db.update_permanent_station(station_id, approved=True)
            elif station_type == "temp":
                ok = self.application.db.update_temporary_station(station_id, approved=True)
            if ok:
                # Update OK, refresh the page
                self.set_status(200)
                self.write(json.dumps({"message": "Station approved.", "redirect_url": "/admin/approval"}))
                return
            else:
                self.set_status(500)
                self.write(
                    json.dumps({"message": "Failed to update the station. Please check the logs for more details."}))
                return

        # Check for Deny action
        elif action == "Deny":
            ok = False
            if station_type == "perm":
                ok = self.application.db.delete_permanent_station(station_id)
            elif station_type == "temp":
                ok = self.application.db.delete_temporary_station(station_id)
            if ok:
                # Update OK, refresh the page
                self.set_status(200)
                self.write(json.dumps({"message": "Station delected.", "redirect_url": "/admin/approval"}))
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
