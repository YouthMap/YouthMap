import asyncio
import json

import tornado

from core.utils import verify_recaptcha
from requesthandlers.base import BaseHandler


class LoginHandler(BaseHandler):
    """Handler for login page, includes POSTing username and password as well as rendering the HTML"""

    async def get(self):
        # Get the 'next' parameter from the query string if there was one. This is where we are going to forward to on
        # successful login. Default to the admin dashboard.
        next_url = self.get_argument("next", "/admin")

        # Redirect to the 'next' URL if we are already logged in, as we can just skip the login
        if self.current_user:
            self.redirect(next_url)
            return

        # Get data we need to include in the template
        executor = tornado.ioloop.IOLoop.current()
        insecure_user_present = await executor.run_in_executor(None,
                                                               lambda: self.application.db.is_insecure_user_present())
        config = await executor.run_in_executor(None, lambda: self.application.db.get_config())
        enable_captcha = config.enable_captcha
        recaptcha_site_key = config.recaptcha_site_key

        # Render the template. This includes a hidden field with the 'next' URL in it so we can get it back again in the
        # POST method.
        self.render("login.html", next=next_url, insecure_user_present=insecure_user_present,
                    enable_captcha=enable_captcha, recaptcha_site_key=recaptcha_site_key)

    async def post(self):
        """Handles POST requests for login page. If successful a session token will be created, stored in a cookie, and
        the user will be redirected to the admin page."""

        # Brief delay to make spamming attacks less viable
        await asyncio.sleep(1)

        self.set_header("Content-Type", "application/json")
        executor = tornado.ioloop.IOLoop.current()

        # Check CAPTCHA if required
        config = await executor.run_in_executor(None, lambda: self.application.db.get_config())
        if config.enable_captcha:
            recaptcha_token = self.get_argument("recaptcha_token", None)
            captcha_ok = await executor.run_in_executor(None, lambda: verify_recaptcha(
                config.recaptcha_secret_key, recaptcha_token))
            if not captcha_ok:
                self.set_status(401)
                self.write(json.dumps({"message": "CAPTCHA verification failed."}))
                return

        # Get request arguments
        username = self.get_argument("username")
        password = self.get_argument("password")
        next_url = self.get_argument("next", "/admin")

        # Ensure next_url is relative and is not sending people off-site to a clone. If it looks dodgy, just replace it
        # with our own admin page
        if not next_url.startswith("/") or "://" in next_url:
            next_url = "/admin"

        # Check that the username and password match a known user
        user_id = await executor.run_in_executor(None, lambda: self.application.db.verify_user(username,
                                                                                               password))

        if user_id:
            session_token = await executor.run_in_executor(None,
                                                           lambda: self.application.db.create_user_session(
                                                               user_id))
            self.set_secure_cookie("session_token", session_token)
            self.set_status(200)
            self.write(json.dumps({"redirect_url": next_url}))
            return
        else:
            self.set_status(401)
            self.write(json.dumps({"message": "The username and password you provided were incorrect."}))
            return
