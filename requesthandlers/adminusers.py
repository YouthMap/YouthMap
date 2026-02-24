import tornado

from requesthandlers.base import BaseHandler


class AdminUsersHandler(BaseHandler):
    """Handler for admin user list page"""

    @tornado.web.authenticated
    async def get(self):
        # Deny access if we are not a super-admin
        executor = tornado.ioloop.IOLoop.current()
        user = await executor.run_in_executor(None,
                                              lambda: self.application.db.get_user(self.current_user))
        if not user.super_admin:
            self.write("You do not have permission to access this page.")
            return

        # Get data we need to include in the template
        users = await executor.run_in_executor(None, lambda: self.application.db.get_all_users())

        # Render the template
        self.render("adminusers.html", users=users, current_user=user)
