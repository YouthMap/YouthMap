from datetime import datetime

import tornado

from requesthandlers.base import BaseHandler


class AdminEventsHandler(BaseHandler):
    """Handler for admin event list page"""

    @tornado.web.authenticated
    def get(self):
        # Get data we need to include in the template
        events = sorted(self.application.db.get_all_events(), key=lambda x: x.start_time)
        events_by_type = {"Past": [x for x in events if datetime.now() > x.end_time],
                                 "Current": [x for x in events if x.start_time <= datetime.now() <= x.end_time],
                                 "Future": [x for x in events if datetime.now() < x.start_time]}

        # Render the template
        self.render("adminevents.html", events_by_type=events_by_type)
