import tornado

from requesthandlers.base import BaseHandler


class ChangePasswordHandler(BaseHandler):
    """Handler for change password page, includes POSTing the passwords as well as rendering the HTML"""

    @tornado.web.authenticated
    def get(self):
        # Redirect to login page if we don't have a current user. (The @tornado.web.authenticated annotation should do
        # this for us, I think?)
        if not self.current_user:
            self.redirect("/login")
            return

        # Get values we need to include in the template
        username = self.application.db.get_user(self.current_user).username

        # Render the template
        self.render("changepassword.html", username=username)

    def post(self):
        """POST request handler, takes user-submitted form data and sets their password if possible."""

        # Get request arguments
        old_password = self.get_argument("old_password")
        new_password = self.get_argument("new_password")
        new_password_2 = self.get_argument("new_password_2")

        # Check new passwords match and that old password is correct
        if new_password != new_password_2:
            self.write("New password entries were not the same")
            return
        username = self.application.db.get_user(self.current_user).username
        user_id = self.application.db.verify_user(username, old_password)
        if not user_id:
            self.write("Old password was incorrect")
            return

        # OK to proceed, set the password in the database
        self.application.db.update_user(self.current_user, password=new_password)
        self.write("Password changed")