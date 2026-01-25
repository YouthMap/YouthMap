import tornado

from requesthandlers.base import BaseHandler


class AdminEventsHandler(BaseHandler):
    """Handler for admin event management page"""

    @tornado.web.authenticated
    def get(self):
        # Get data we need to include in the template
        events = self.application.db.get_all_events()

        # Render the template
        self.render("adminevents.html", events=events)

    @tornado.web.authenticated
    def post(self):
        """Handles POST requests for event management page. This supports three 'actions' depending on whether the Update
        or Delete button was clicked for an existing event, or the Create button was clicked for a new event, and provides
        the updated data to insert back into the database."""

        # Get the action we have been asked to do
        action = self.get_argument("action")

        # Check for Delete action
        if action == "Delete":
            # Get request arguments. For a Delete we only need the ID
            event_id = self.get_argument("id")

            # Process the delete
            ok = self.application.db.delete_event(event_id)
            if ok:
                # Delete OK, just reload the page which will have the new data in it
                self.redirect("/admin/events")
            else:
                self.write("Failed to delete event")

        # Check for Update action
        elif action == "Update":
            # Get request arguments. For an update we need ID plus......
            # TODO
            event_id = self.get_argument("id")

            self.write("not implemented yet")

        # Check for Create action
        elif action == "Create":
            # Get request arguments. For a create we need......
            # TODO

            self.write("not implemented yet")

        else:
            self.write("Invalid action '" + action + "'")
