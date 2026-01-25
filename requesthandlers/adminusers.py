import tornado

from requesthandlers.base import BaseHandler


class AdminUsersHandler(BaseHandler):
    """Handler for admin user list page"""

    @tornado.web.authenticated
    def get(self):
        # Deny access if we are not a super-admin
        user = self.application.db.get_user(self.current_user)
        if not user.super_admin:
            self.write("You do not have permission to access this page.")
            return

        # Get data we need to include in the template
        users = self.application.db.get_all_users()

        # Render the template
        self.render("adminusers.html", users=users, current_user=user)
