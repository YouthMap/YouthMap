import tornado

from requesthandlers.base import BaseHandler


class AdminHandler(BaseHandler):
    """Handler for admin dashboard"""

    @tornado.web.authenticated
    def get(self):
        # Get values we need to include in the template
        username = self.application.db.get_user(self.current_user).username

        # Render the template
        self.render("admin.html", username=username)
