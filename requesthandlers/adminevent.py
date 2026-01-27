from datetime import datetime

import tornado

from core.utils import get_all_icons
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
        event = self.application.db.get_event(event_id) if not creating_new else None
        event_bands = self.application.db.get_event_bands(event_id) if event else None
        event_modes = self.application.db.get_event_modes(event_id) if event else None
        event_stations = self.application.db.get_event_stations(event_id) if event else None
        all_bands = self.application.db.get_all_bands()
        all_modes = self.application.db.get_all_modes()
        all_icons = get_all_icons()

        # Render the template
        self.render("adminevent.html", event=event, event_bands=event_bands, event_modes=event_modes,
                    event_stations=event_stations, creating_new=creating_new, all_bands=all_bands, all_modes=all_modes,
                    all_icons=all_icons)

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
            # Get request arguments
            name = self.get_argument("name")
            start_time = datetime.strptime(self.get_argument("start_time"), "%Y-%m-%dT%H:%M")
            end_time = datetime.strptime(self.get_argument("end_time"), "%Y-%m-%dT%H:%M")
            band_ids = []
            if self.get_argument("bands[]", None):
                band_ids = [int(x) for x in self.request.arguments["bands[]"]]
            mode_ids = []
            if self.get_argument("modes[]", None):
                mode_ids = [int(x) for x in self.request.arguments["modes[]"]]
            icon = self.get_argument("icon")
            color = self.get_argument("color")
            notes_template = self.get_argument("notes_template", None)
            notes_template = notes_template if notes_template else ""
            url_slug = self.get_argument("url_slug", None)
            url_slug = url_slug if url_slug else ""
            public = True if self.get_argument("public", None) else False
            rsgb_event = True if self.get_argument("rsgb_event", None) else False

            # Process the update
            ok = self.application.db.update_event(event_id, name=name, start_time=start_time, end_time=end_time,
                                                  band_ids=band_ids, mode_ids=mode_ids, icon=icon, color=color,
                                                  notes_template=notes_template, url_slug=url_slug, public=public,
                                                  rsgb_event=rsgb_event)
            if ok:
                # Update OK, just reload the page which will have the new data in it
                self.redirect("/admin/event/" + slug)
            else:
                self.write("Failed to update event")
                return

        # Check for Create action
        elif action == "Create":
            # Get request arguments.
            name = self.get_argument("name")
            start_time = datetime.strptime(self.get_argument("start_time"), "%Y-%m-%dT%H:%M")
            end_time = datetime.strptime(self.get_argument("end_time"), "%Y-%m-%dT%H:%M")
            band_ids = []
            if self.get_argument("bands[]", None):
                band_ids = [int(x) for x in self.request.arguments["bands[]"]]
            mode_ids = []
            if self.get_argument("modes[]", None):
                mode_ids = [int(x) for x in self.request.arguments["modes[]"]]
            icon = self.get_argument("icon")
            color = self.get_argument("color")
            notes_template = self.get_argument("notes_template", None)
            notes_template = notes_template if notes_template else ""
            url_slug = self.get_argument("url_slug", None)
            url_slug = url_slug if url_slug else ""
            public = True if self.get_argument("public", None) else False
            rsgb_event = True if self.get_argument("rsgb_event", None) else False

            # Process the create action
            new_event_id = self.application.db.add_event(name=name, start_time=start_time, end_time=end_time,
                                                         band_ids=band_ids, mode_ids=mode_ids, icon=icon, color=color,
                                                         notes_template=notes_template, url_slug=url_slug,
                                                         public=public, rsgb_event=rsgb_event)
            if new_event_id:
                # Create OK, just reload the page which will have the new data in it
                self.redirect("/admin/event/" + str(new_event_id))
            else:
                self.write("Failed to update event")
                return

        else:
            self.write("Invalid action '" + action + "'")
