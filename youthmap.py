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
            (r"/", MapHandler),
            (r"/view/station/(perm|temp)/([^/]+)", ViewStationHandler),
            (r"/edit/station/(perm|temp)/([^/]+)", EditStationHandler),
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
            (r"/admin", AdminHandler),
            (r"/admin/users", AdminUsersHandler),
            (r"/admin/user/([^/]+)", AdminUserHandler),
            (r"/admin/events", AdminEventsHandler),
            (r"/admin/event/([^/]+)", AdminEventHandler),
            (r"/admin/stations", AdminStationsHandler),
            (r"/admin/station/temp/([^/]+)", AdminStationTempHandler),
            (r"/admin/station/perm/([^/]+)", AdminStationPermHandler),
            (r"/upload/(.*)", StaticFileHandler, {"path": os.path.join(os.path.dirname(__file__), "data/upload"), "cache_time": 120}),
            (r"/(.*)", StaticFileHandler, {"path": os.path.join(os.path.dirname(__file__), "static")})
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
