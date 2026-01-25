from requesthandlers.base import BaseHandler


class LoginHandler(BaseHandler):
    """Handler for login page, includes POSTing username and password as well as rendering the HTML"""

    def get(self):
        # Redirect to login page if we don't have a current user. (The @tornado.web.authenticated annotation should do
        # this for us, I think?)
        if self.current_user:
            self.redirect("/admin")
            return

        # Render the template
        self.render("login.html")

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
