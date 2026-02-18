import json

import tornado

from requesthandlers.base import BaseHandler


class AdminConfigHandler(BaseHandler):
    """Handler for admin site config editing page"""

    @tornado.web.authenticated
    def get(self):
        """Get the HTML page containing the form"""

        # Deny access if we are not a super-admin
        user = self.application.db.get_user(self.current_user)
        if not user.super_admin:
            self.write("You do not have permission to access this page.")
            return

        # Get data we need to include in the template
        config = self.application.db.get_config()

        # Render the template
        self.render("adminconfig.html", config=config)

    @tornado.web.authenticated
    def post(self):
        """Handles POST requests for the config page. Unlike most other pages, the 'action' is irrelevant here as config
        can only ever be updated, never created or deleted."""

        self.set_header("Content-Type", "application/json")

        # Deny access if we are not a super-admin
        user = self.application.db.get_user(self.current_user)
        if not user.super_admin:
            self.set_status(400)
            self.write(json.dumps({"message": "You do not have permission to access this page."}))
            return

        # Get request arguments
        base_url = self.get_argument("base_url", None)

        enable_mail = True if self.get_argument("enable_mail", None) else False
        mail_server_host = self.get_argument("mail_server_host", None)
        mail_server_port = int(self.get_argument("mail_server_port", "0"))
        mail_username = self.get_argument("mail_username", None)
        mail_password = self.get_argument("mail_password", None)
        mail_sender = self.get_argument("mail_sender", None)

        enable_captcha = True if self.get_argument("enable_captcha", None) else False
        recaptcha_key = self.get_argument("recaptcha_key", None)

        # Check for validity
        if enable_mail and not (
                mail_sender and mail_username and mail_password and mail_server_host and mail_server_port > 0):
            self.set_status(400)
            self.write(json.dumps({
                "message": "You must supply a full set of SMTP server information and credentials if you want to enable email supprt."}))
            return
        if enable_captcha and not recaptcha_key:
            self.set_status(400)
            self.write(json.dumps({
                "message": "You must supply a reCAPTCHA key if you want to enable CAPTCHA supprt."}))
            return

        # Process the update
        ok = self.application.db.update_config(base_url=base_url, enable_mail=enable_mail, mail_sender=mail_sender,
                                               mail_username=mail_username, mail_password=mail_password,
                                               mail_server_host=mail_server_host, mail_server_port=mail_server_port,
                                               enable_captcha=enable_captcha, recaptcha_key=recaptcha_key)
        if ok:
            # Update OK
            self.set_status(200)
            self.write(json.dumps(
                {"message": "Config updated. Returning you to the admin panel...", "redirect_url": "/admin"}))
            return
        else:
            self.set_status(500)
            self.write(
                json.dumps({"message": "Failed to update the config. Please check the logs for more details."}))
            return
