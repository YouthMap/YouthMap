import json
from datetime import datetime

import tornado

from core.utils import get_all_icons, get_default_event_start_time, get_default_event_end_time
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
        all_bands = self.application.db.get_all_bands()
        all_modes = self.application.db.get_all_modes()
        all_icons = get_all_icons()
        default_start = get_default_event_start_time()
        default_end = get_default_event_end_time()

        # Render the template
        if event:
            self.render("adminevent.html", event=event, creating_new=creating_new, all_bands=all_bands,
                        all_modes=all_modes, all_icons=all_icons, default_start=default_start, default_end=default_end)
        else:
            self.write("Event not found.")

    @tornado.web.authenticated
    def post(self, slug):
        """Handles POST requests for event editing page. This supports three 'actions' depending on whether the Update
        or Delete button was clicked for an existing event, or the Create button was clicked for a new event, and
        provides the updated data to insert back into the database. The slug here is the event ID, so e.g. the URL can
        be /admin/event/1 to edit event 1. A special slug of 'new' is also allowed, which sets up the form to create an
        event rather than to edit one."""

        self.set_header("Content-Type", "application/json")

        event_id = int(slug) if slug != "new" else None

        # Get the action we have been asked to do
        action = self.get_argument("action")

        # Check for Delete action
        if action == "Delete":
            # Process the delete action
            ok = self.application.db.delete_event(event_id)
            if ok:
                # Delete OK
                self.set_status(200)
                self.write(json.dumps(
                    {"message": "Event deleted. Returning you to the events list...", "redirect_url": "/admin/events"}))
                return
            else:
                self.set_status(500)
                self.write(
                    json.dumps({"message": "Failed to delete the event. Please check the logs for more details."}))
                return

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
            url_slug = self.get_argument("url_slug")
            public = True if self.get_argument("public", None) else False
            rsgb_event = True if self.get_argument("rsgb_event", None) else False

            # Check for sensible times
            if start_time > end_time:
                self.set_status(400)
                self.write(json.dumps({
                    "message": "Your event cannot start after it ends. Please check your time entries carefully."}))
                return

            # Catch a uniqueness violation before it happens, so we can explicitly warn the user about this
            other_events = [e for e in self.application.db.get_all_events() if e.id != event_id]
            if any(e.name.lower() == name.lower() for e in other_events):
                self.set_status(400)
                self.write(json.dumps({
                    "message": "Another event is already called '" + name + "'. Event names must be unique and are case-insensitive."}))
                return
            if not self.ensure_url_slug_validity(url_slug, other_events):
                return

            # Process the update
            ok = self.application.db.update_event(event_id, name=name, start_time=start_time, end_time=end_time,
                                                  band_ids=band_ids, mode_ids=mode_ids, icon=icon, color=color,
                                                  notes_template=notes_template, url_slug=url_slug, public=public,
                                                  rsgb_event=rsgb_event)
            if ok:
                # Update OK
                self.set_status(200)
                self.write(json.dumps(
                    {"message": "Event updated. Returning you to the events list...", "redirect_url": "/admin/events"}))
                return
            else:
                self.set_status(500)
                self.write(
                    json.dumps({"message": "Failed to update the event. Please check the logs for more details."}))
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
            url_slug = self.get_argument("url_slug")
            public = True if self.get_argument("public", None) else False
            rsgb_event = True if self.get_argument("rsgb_event", None) else False

            # Check for sensible times
            if start_time > end_time:
                self.set_status(400)
                self.write(json.dumps({
                    "message": "Your event cannot start after it ends. Please check your time entries carefully."}))
                return

            # Catch a uniqueness violation before it happens, so we can explicitly warn the user about this
            other_events = self.application.db.get_all_events()
            if any(e.name.lower() == name.lower() for e in other_events):
                self.set_status(400)
                self.write(json.dumps({
                    "message": "Another event is already called '" + name + "'. Event names must be unique and are case-insensitive."}))
                return
            if not self.ensure_url_slug_validity(url_slug, other_events):
                return

            # Process the create action
            new_event_id = self.application.db.add_event(name=name, start_time=start_time, end_time=end_time,
                                                         band_ids=band_ids, mode_ids=mode_ids, icon=icon, color=color,
                                                         notes_template=notes_template, url_slug=url_slug,
                                                         public=public, rsgb_event=rsgb_event)
            if new_event_id:
                # Create OK
                self.set_status(200)
                self.write(json.dumps(
                    {"message": "Event created. Returning you to the events list...", "redirect_url": "/admin/events"}))
                return
            else:
                self.set_status(500)
                self.write(
                    json.dumps({"message": "Failed to create the event. Please check the logs for more details."}))
                return

        else:
            self.set_status(400)
            self.write(json.dumps({"message": "Invalid action '" + action + "'"}))
            return

    def ensure_url_slug_validity(self, url_slug, other_events):
        """Ensures that a URL slug is valid. It must not match the slug of any existing event, or the name of a
        permanent station type, or another page such as "admin" or "login" that means it would not work. Supply the
        URL slug to test, and "other_events" - for a new event being added, this should be all existing events, whereas
        when updating an event, this should be all *other* events to avoid finding a conflict with itself. The method
        sets a status code and writes the error message where required, then returns true if it was validated and false
        if it was not."""

        if any(e.url_slug.lower() == url_slug.lower() for e in other_events):
            self.set_status(400)
            self.write(json.dumps({
                "message": "Another event already has the URL slug '" + url_slug + "'. Event URL slugs must be unique and are case-insensitive."}))
            return False

        if any(t.name.lower() == url_slug.lower() for t in self.application.db.get_all_permanent_station_types()):
            self.set_status(400)
            self.write(json.dumps({
                "message": "A permanent station type of '" + url_slug + "' is in use. Event URL slugs cannot conflict with permanent station types, and both are case-insensitive."}))
            return False

        if any(slug == url_slug.lower() for slug in ["admin", "login", "logout"]):
            self.set_status(400)
            self.write(json.dumps({
                "message": "A URL slug of '" + url_slug + "' would conflict with an internal site page."}))
            return False

        if url_slug == "":
            self.set_status(400)
            self.write(json.dumps({"message": "A URL slug cannot be blank."}))
            return False

        return True
