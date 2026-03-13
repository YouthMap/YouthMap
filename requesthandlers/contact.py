import asyncio
import json

import tornado

from core.validation import validate_free_text, validate_email_address
from mail.mailer import notify_admins_contact_message
from requesthandlers.base import BaseHandler


class ContactHandler(BaseHandler):
    """Handler for the general contact page"""

    async def get(self):
        """Generate the page."""

        # Get data we need to include in the template
        executor = tornado.ioloop.IOLoop.current()
        config = await executor.run_in_executor(None, lambda: self.application.db.get_config())
        enable_captcha = config.enable_captcha
        recaptcha_site_key = config.recaptcha_site_key

        self.render("contact.html", enable_captcha=enable_captcha, recaptcha_site_key=recaptcha_site_key)

    async def post(self):
        """Handles POST requests for the contact form. Sends the message to all administrators via email."""

        # Brief delay to make spamming attacks less viable
        await asyncio.sleep(1)

        self.set_header("Content-Type", "application/json")
        executor = tornado.ioloop.IOLoop.current()

        # Get and validate request arguments
        name, err_name = validate_free_text(self.get_argument("name", "") or "", "Name", max_length=200)
        email, err_email = validate_email_address(self.get_argument("email", "") or "")
        message, err_message = validate_free_text(self.get_argument("message", "") or "", "Message", max_length=5000)

        err = next((x for x in [err_name, err_email, err_message] if x is not None), None)
        if err:
            self.set_status(400)
            self.write(json.dumps({"message": err}))
            return

        if not message:
            self.set_status(400)
            self.write(json.dumps({"message": "A message is required."}))
            return

        await executor.run_in_executor(None,
                                       lambda: notify_admins_contact_message(self.application.db, name, email,
                                                                             message))

        self.set_status(200)
        self.write(json.dumps({
            "message": "Thank you. Your message has been sent to the administrators. Redirecting you back to the home page...",
            "redirect_url": "/"}))
