from requesthandlers.base import BaseHandler


class LoginHandler(BaseHandler):
    """Handler for login page, includes POSTing username and password as well as rendering the HTML"""

    def get(self):
        # Get the 'next' parameter from the query string if there was one. This is where we are going to forward to on
        # successful login. Default to the admin dashboard.
        next_url = self.get_argument("next", "/admin")

        # Redirect to the 'next' URL if we are already logged in, as we can just skip the login
        if self.current_user:
            self.redirect(next_url)
            return

        # Get data we need to include in the template
        insecure_user_present = self.application.db.is_insecure_user_present()

        # Render the template. This includes a hidden field with the 'next' URL in it so we can get it back again in the
        # POST method.
        self.render("login.html", next=next_url, insecure_user_present=insecure_user_present)

    def post(self):
        """Handles POST requests for login page. If successful a session token will be created, stored in a cookie, and
        the user will be redirected to the admin page."""

        # Get request arguments
        username = self.get_argument("username")
        password = self.get_argument("password")
        next_url = self.get_argument("next", "/admin")

        # Check that the username and password match a known user
        user_id = self.application.db.verify_user(username, password)

        if user_id:
            session_token = self.application.db.create_user_session(user_id)
            self.set_secure_cookie("session_token", session_token)
            self.redirect(next_url)
        else:
            self.write("Invalid credentials")
