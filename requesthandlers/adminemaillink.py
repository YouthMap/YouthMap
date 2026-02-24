import json

import tornado

from mail.mailer import notify_owner_station_approved, notify_owner_station_approval_revoked, \
    notify_owner_station_deleted
from requesthandlers.base import BaseHandler


class AdminEmailLinkHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        """Handler for buttons in emails sent to the site administrators. These allow changing the approval status or
        deleting stations. The GET request takes three arguments: action, station_type (perm or temp) and id. The user must
        be authenticated, so when they click the link in their email it will open a browser window, and if they're not
        authenticated in that session they will get bounced to the login page. The GET simply presents a summary of the
        requested action, with a button to click to action it. The three arguments are simply embedded in the page in
        hidden form elements."""

        # Get params
        action = self.get_argument("action", None)
        station_type = self.get_argument("station_type", None)
        station_id = self.get_argument("id", None)

        # Check params are suitable
        if not action or not station_type or not station_id or (station_type != "perm" and station_type != "temp"):
            self.set_status(400)
            self.write("Incorrect parameters provided.")
            return

        self.render("adminemaillink.html", action=action, station_type=station_type, station_id=station_id)

    @tornado.web.authenticated
    def post(self):
        """POST handler to confirm the user's desire. Because visitors to this page may have been clicking links
        from emails that are old, and because there can be several administrators reacting to emails at the same time, the
        POST handler performs a number of checks that most pages don't - e.g. when approving a station, it checks that it is
        not already approved. This saves the station owners from receiving multiple emails to tell them different
        administrators have done the same thing."""

        self.set_header("Content-Type", "application/json")

        # Get params
        action = self.get_argument("action", None)
        station_type = self.get_argument("station_type", None)
        station_id = self.get_argument("id", None)

        # Check params are suitable
        if not action or not station_type or not station_id or (station_type != "perm" and station_type != "temp"):
            self.set_status(400)
            self.write(json.dumps({"message": "Incorrect parameters provided."}))
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
                self.write(json.dumps({
                                          "message": "The station has already been deleted. Perhaps another administrator got there first?"}))
                return
            else:
                self.set_status(400)
                self.write(json.dumps(
                    {"message": "The station does not exist. Perhaps it was already deleted by someone else?"}))
                return

        # Process the action
        if action == "approve":
            if station.approved:
                self.set_status(409)
                self.write(json.dumps(
                    {"message": "The station was already approved. Perhaps another administrator got there first?"}))
                return

            ok = False
            if station_type == "perm":
                ok = self.application.db.update_permanent_station(station_id, approved=True)
            elif station_type == "temp":
                ok = self.application.db.update_temporary_station(station_id, approved=True)
            if ok:
                # Show success page and email the station owner
                self.set_status(200)
                self.write(json.dumps({"message": "You have successfully approved this station."}))
                notify_owner_station_approved(self.application.db, station)
                return
            else:
                self.set_status(500)
                self.write(json.dumps({
                                          "message": "An error occurred while approving this station. Please check the logs for more details."}))
                return

        if action == "unapprove":
            if not station.approved:
                self.set_status(409)
                self.write(json.dumps(
                    {"message": "The station was not approved anyway. Perhaps another administrator got there first?"}))
                return

            ok = False
            if station_type == "perm":
                ok = self.application.db.update_permanent_station(station_id, approved=False)
            elif station_type == "temp":
                ok = self.application.db.update_temporary_station(station_id, approved=False)
            if ok:
                # Show success page and email the station owner
                self.set_status(200)
                self.write(json.dumps({"message": "You have successfully revoked the approved state of this station."}))
                notify_owner_station_approval_revoked(self.application.db, station)
                return
            else:
                self.set_status(500)
                self.write(json.dumps({
                                          "message": "An error occurred while revoking the approved state of this station. Please check the logs for more details."}))
                return

        if action == "delete":
            ok = False
            if station_type == "perm":
                ok = self.application.db.delete_permanent_station(station_id)
            elif station_type == "temp":
                ok = self.application.db.delete_temporary_station(station_id)
            if ok:
                # Show success page and email the station owner
                self.set_status(200)
                self.write(json.dumps({"message": "You have successfully deleted the station."}))
                notify_owner_station_deleted(self.application.db, station)
                return
            else:
                self.set_status(500)
                self.write(json.dumps({
                                          "message": "An error occurred while deleting the station. Please check the logs for more details."}))
                return
