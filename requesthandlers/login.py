from requesthandlers.base import BaseHandler


class LoginHandler(BaseHandler):
    """Handler for login page, includes POSTing username and password as well as rendering the HTML"""

    def get(self):
        # Redirect to the admin page if we are already logged in, as we can just skip this one
        if self.current_user:
            self.redirect("/admin")
            return

        # Get data we need to include in the template
        insecure_user_present = self.application.db.is_insecure_user_present()

        # Render the template
        self.render("login.html", insecure_user_present=insecure_user_present)

    def post(self):
        """Handles POST requests for login page. If successful a session token will be created, stored in a cookie, and
        the user will be redirected to the admin page."""

        # Get request arguments
        username = self.get_argument("username")
        password = self.get_argument("password")

        # Check that the username and password match a known user
        user_id = self.application.db.verify_user(username, password)

        if user_id:
            session_token = self.application.db.create_user_session(user_id)
            self.set_secure_cookie("session_token", session_token)
            self.redirect("/admin")
        else:
            self.write("Invalid credentials")
