import tornado

from requesthandlers.base import BaseHandler


class AdminStationTempHandler(BaseHandler):
    """Handler for admin temporary station editing page"""

    @tornado.web.authenticated
    def get(self, slug):
        """The slug here is the temporary station ID, so e.g. the URL can be /admin/station/temp/1 to edit temporary
        station 1. A special slug of 'new' is also allowed, which sets up the form to create a temporary station rather
        than to edit one."""

        station_id = int(slug) if slug != "new" else None
        creating_new = (slug == "new")

        # Get data we need to include in the template
        station = self.application.db.get_temporary_station(station_id) if not creating_new else None

        # Render the template
        self.render("adminstationtemp.html", station=station, creating_new=creating_new)

    @tornado.web.authenticated
    def post(self, slug):
        """Handles POST requests for temporary station editing page. This supports three 'actions' depending on whether
        the Update or Delete button was clicked for an existing station, or the Create button was clicked for a new
        station, and provides the updated data to insert back into the database. The slug here is the temporary station
        ID, so e.g. the URL can be /admin/station/temp/1 to edit temporary station 1. A special slug of 'new' is also
        allowed, which sets up the form to create a temporary station rather than to edit one."""

        station_id = int(slug) if slug != "new" else None

        # Get the action we have been asked to do
        action = self.get_argument("action")

        # Check for Delete action
        if action == "Delete":
            # Process the delete action
            ok = self.application.db.delete_temporary_station(station_id)
            if ok:
                # Delete OK, just reload the page which will have the new data in it
                self.redirect("/admin/stations")
            else:
                self.write("Failed to delete station")

        # Check for Update action
        elif action == "Update":
            # Get request arguments. For an update we need......
            # TODO

            self.write("not implemented yet")

        # Check for Create action
        elif action == "Create":
            # Get request arguments. For a create we need......
            # TODO

            self.write("not implemented yet")

        else:
            self.write("Invalid action '" + action + "'")
