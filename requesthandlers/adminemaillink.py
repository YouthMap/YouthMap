from datetime import datetime

import tornado

from requesthandlers.base import BaseHandler


class AdminEmailLinkHandler(BaseHandler):
    """Handler for buttons in emails sent to the site administrators. These allow changing the approval status or
    deleting stations. Since we can't POST from an email, these are implemented with a get request which takes three
    arguments: action, station_type (perm or temp) and id. The user must be authenticated, so when they click the link
    in their email it will open a browser window, and if they're not authenticated in that session they will get bounced
    to the login page."""

    @tornado.web.authenticated
    def get(self):
        # Get params
        action = self.get_argument("action", None)
        station_type = self.get_argument("station_type", None)
        station_id = self.get_argument("id", None)

        # Check params are suitable
        if not action or not station_type or not station_id or (station_type != "perm" and station_type != "temp"):
            self.set_status(400)
            self.render("adminemaillink.html", success=False, message="Incorrect parameters provided.")
            return

        # Check the station exists
        station_id = int(station_id)
        station = None
        if station_type == "perm":
            station = self.application.db.get_permanent_station(station_id)
        elif station_type == "temp":
            station = self.application.db.get_temporary_station(station_id)
        if not station:
            if action == "delete":
                self.set_status(409)
                self.render("adminemaillink.html", success=True, message="The station has already been deleted. Perhaps another administrator got there first?")
                return
            else:
                self.set_status(400)
                self.render("adminemaillink.html", success=False, message="The station does not exist. Perhaps it was already deleted by someone else?")
                return

        # Process the action
        if action == "approve":
            if station.approved:
                self.set_status(409)
                self.render("adminemaillink.html", success=True, message="The station was already approved. Perhaps another administrator got there first?")
                return

            ok = False
            if station_type == "perm":
                ok = self.application.db.update_permanent_station(station_id, approved=True)
            elif station_type == "temp":
                ok = self.application.db.update_temporary_station(station_id, approved=True)
            if ok:
                self.set_status(200)
                self.render("adminemaillink.html", success=True, message="You have successfully approved this station.")
                return
            else:
                self.set_status(500)
                self.render("adminemaillink.html", success=False, message="An error occurred while approving this station. Please check the logs for more details.")
                return

        if action == "unapprove":
            if not station.approved:
                self.set_status(409)
                self.render("adminemaillink.html", success=True, message="The station was not approved anyway. Perhaps another administrator got there first?")
                return

            ok = False
            if station_type == "perm":
                ok = self.application.db.update_permanent_station(station_id, approved=False)
            elif station_type == "temp":
                ok = self.application.db.update_temporary_station(station_id, approved=False)
            if ok:
                self.set_status(200)
                self.render("adminemaillink.html", success=True, message="You have successfully revoked the approved state of this station.")
                return
            else:
                self.set_status(500)
                self.render("adminemaillink.html", success=False, message="An error occurred while revoking the approved state of this station. Please check the logs for more details.")
                return

        if action == "delete":
            ok = False
            if station_type == "perm":
                ok = self.application.db.delete_permanent_station(station_id)
            elif station_type == "temp":
                ok = self.application.db.delete_temporary_station(station_id)
            if ok:
                self.set_status(200)
                self.render("adminemaillink.html", success=True, message="You have successfully deleted the station.")
                return
            else:
                self.set_status(500)
                self.render("adminemaillink.html", success=False, message="An error occurred while deleting the station. Please check the logs for more details.")
                return
