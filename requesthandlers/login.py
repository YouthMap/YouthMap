import json
from time import sleep

from core.utils import verify_recaptcha
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
        enable_captcha = self.application.db.get_config().enable_captcha
        recaptcha_site_key = self.application.db.get_config().recaptcha_site_key

        # Render the template. This includes a hidden field with the 'next' URL in it so we can get it back again in the
        # POST method.
        self.render("login.html", next=next_url, insecure_user_present=insecure_user_present,
                    enable_captcha=enable_captcha, recaptcha_site_key=recaptcha_site_key)

    def post(self):
        """Handles POST requests for login page. If successful a session token will be created, stored in a cookie, and
        the user will be redirected to the admin page."""

        # Brief delay to make spamming attacks less viable
        sleep(1)

        self.set_header("Content-Type", "application/json")

        # Check CAPTCHA if required
        if self.application.db.get_config().enable_captcha:
            recaptcha_token = self.get_argument("recaptcha_token", None)
            if not verify_recaptcha(self.application.db.get_config().recaptcha_secret_key, recaptcha_token):
                self.set_status(401)
                self.write(json.dumps({"message": "CAPTCHA verification failed."}))
                return

        # Get request arguments
        username = self.get_argument("username")
        password = self.get_argument("password")
        next_url = self.get_argument("next", "/admin")

        # Check that the username and password match a known user
        user_id = self.application.db.verify_user(username, password)

        if user_id:
            session_token = self.application.db.create_user_session(user_id)
            self.set_secure_cookie("session_token", session_token)
            self.set_status(200)
            self.write(json.dumps({"message": "Logged in successfully.", "redirect_url": next_url}))
            return
        else:
            self.set_status(401)
            self.write(json.dumps({"message": "The username and password you provided were incorrect."}))
            return
