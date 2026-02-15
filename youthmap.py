import logging
import os
import secrets
import sys

import tornado.ioloop
import tornado.web
from tornado.web import StaticFileHandler

from core.config import HTTP_PORT
from database import Database
from requesthandlers.admin import AdminHandler
from requesthandlers.adminevent import AdminEventHandler
from requesthandlers.adminevents import AdminEventsHandler
from requesthandlers.adminstationperm import AdminStationPermHandler
from requesthandlers.adminstations import AdminStationsHandler
from requesthandlers.adminstationtemp import AdminStationTempHandler
from requesthandlers.adminuser import AdminUserHandler
from requesthandlers.adminusers import AdminUsersHandler
from requesthandlers.createstation import CreateStationHandler
from requesthandlers.createstationtype import CreateStationTypeHandler
from requesthandlers.editstation import EditStationHandler
from requesthandlers.login import LoginHandler
from requesthandlers.logout import LogoutHandler
from requesthandlers.map import MapHandler
from requesthandlers.viewstation import ViewStationHandler


class YouthMap(tornado.web.Application):
    """Main application class"""

    def __init__(self):
        # Set up logging
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        root.addHandler(handler)

        logging.info("Setting up database...")
        self.db = Database()

        logging.info("Setting up web server...")
        handlers = [
            # Normal home URL for the map with no slug provided
            (r"/", MapHandler),
            # User-accessible pages to view, edit and create stations
            (r"/view/station/(perm|temp)/([^/]+)", ViewStationHandler),
            (r"/edit/station/(perm|temp)/([^/]+)", EditStationHandler),
            (r"/create/station/type", CreateStationTypeHandler),
            (r"/create/station/(perm|temp)", CreateStationHandler),
            # Authentication-related pages
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
            # Admin dashboard and management pages
            (r"/admin", AdminHandler),
            (r"/admin/users", AdminUsersHandler),
            (r"/admin/user/([^/]+)", AdminUserHandler),
            (r"/admin/events", AdminEventsHandler),
            (r"/admin/event/([^/]+)", AdminEventHandler),
            (r"/admin/stations", AdminStationsHandler),
            (r"/admin/station/temp/([^/]+)", AdminStationTempHandler),
            (r"/admin/station/perm/([^/]+)", AdminStationPermHandler),
            # Uploads area
            (r"/upload/(.*)", StaticFileHandler, {"path": os.path.join(os.path.dirname(__file__), "data/upload")}),
            # Static CSS/JS/image assets
            (r"/static/(.*)", StaticFileHandler, {"path": os.path.join(os.path.dirname(__file__), "static")}),
            # If a single slug is provided, and it doesn't match anything above, assume this is an event or permanent
            # station type. Pass it to the main map handler, which will configure the UI to only show stations for that
            # event or of that permanent station type.
            (r"/([^/]+)", MapHandler)
        ]

        settings = {
            "template_path": "templates",
            "cookie_secret": os.environ.get("COOKIE_SECRET", secrets.token_hex(32)),
            "login_url": "/login",
            "debug": True  # todo set false
        }

        super(YouthMap, self).__init__(handlers, **settings)


def main():
    app = YouthMap()
    app.listen(HTTP_PORT)
    logging.info("Listening on port " + str(HTTP_PORT) + ".")
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
