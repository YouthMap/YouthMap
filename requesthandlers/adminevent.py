import tornado

from requesthandlers.base import BaseHandler


class AdminEventHandler(BaseHandler):
    """Handler for admin event editing page"""

    @tornado.web.authenticated
    def get(self, slug):
        """The slug here is the event ID, so e.g. the URL can be /admin/event/1 to edit event 1. A special slug of 'new'
         is also allowed, which sets up the form to create an event rather than to edit one."""

        event_id = int(slug) if slug != "new" else None
        creating_new = (slug == "new")

        # Get data we need to include in the template
        event = self.application.db.get_user(event_id) if not creating_new else None
        all_band_names = [b.name for b in self.application.db.get_all_bands()]
        all_mode_names = [m.name for m in self.application.db.get_all_modes()]

        # Render the template
        self.render("adminevent.html", event=event, creating_new=creating_new, all_band_names=all_band_names, all_mode_names=all_mode_names)

    @tornado.web.authenticated
    def post(self, slug):
        """Handles POST requests for event editing page. This supports three 'actions' depending on whether the Update
        or Delete button was clicked for an existing event, or the Create button was clicked for a new event, and
        provides the updated data to insert back into the database. The slug here is the event ID, so e.g. the URL can
        be /admin/event/1 to edit event 1. A special slug of 'new' is also allowed, which sets up the form to create an
        event rather than to edit one."""

        event_id = int(slug) if slug != "new" else None

        # Get the action we have been asked to do
        action = self.get_argument("action")

        # Check for Delete action
        if action == "Delete":
            # Process the delete action
            ok = self.application.db.delete_event(event_id)
            if ok:
                # Delete OK, just reload the page which will have the new data in it
                self.redirect("/admin/events")
            else:
                self.write("Failed to delete event")

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
