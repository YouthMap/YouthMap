import tornado

from requesthandlers.base import BaseHandler


class AdminEventsHandler(BaseHandler):
    """Handler for admin event list page"""

    @tornado.web.authenticated
    def get(self):
        # Get data we need to include in the template
        events = self.application.db.get_all_events()

        # Render the template
        self.render("adminevents.html", events=events)
