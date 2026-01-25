import logging
import os
import secrets
import sys

import tornado.ioloop
import tornado.web

from core.config import HTTP_PORT
from database import Database
from requesthandlers.admin import AdminHandler
from requesthandlers.updatedetails import UpdateDetailsHandler
from requesthandlers.login import LoginHandler
from requesthandlers.logout import LogoutHandler
from requesthandlers.map import MapHandler


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
            (r"/login", LoginHandler),
            (r"/admin", AdminHandler),
            (r"/logout", LogoutHandler),
            (r"/updatedetails", UpdateDetailsHandler),
        ]

        settings = {
            "template_path": "templates",
            "cookie_secret": os.environ.get("COOKIE_SECRET", secrets.token_hex(32)),
            "login_url": "/login",
        }

        super(YouthMap, self).__init__(handlers, **settings)


def main():
    app = YouthMap()
    app.listen(HTTP_PORT)
    logging.info("Listening on port " + str(HTTP_PORT) + ".")
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
