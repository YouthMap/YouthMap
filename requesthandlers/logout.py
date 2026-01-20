from requesthandlers.base import BaseHandler


class LogoutHandler(BaseHandler):
    """Handler for logout page, just deletes token and redirects to the map"""

    def get(self):
        self.clear_cookie("session_token")
        self.redirect("/")
