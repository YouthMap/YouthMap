import tornado

from requesthandlers.base import BaseHandler


class UpdateDetailsHandler(BaseHandler):
    """Handler for update details page, includes POSTing the new details as well as rendering the HTML"""

    @tornado.web.authenticated
    def get(self):
        # Redirect to login page if we don't have a current user. (The @tornado.web.authenticated annotation should do
        # this for us, I think?)
        if not self.current_user:
            self.redirect("/login")
            return

        # Get data we need to include in the template
        user = self.application.db.get_user(self.current_user)

        # Render the template
        self.render("updatedetails.html", user=user)

    def post(self):
        """POST request handler, takes user-submitted form data and sets their details (including password if possible)."""

        # Get request arguments
        username = self.get_argument("username")
        old_password = self.get_argument("old_password")
        new_password = self.get_argument("new_password")
        new_password_2 = self.get_argument("new_password_2")
        email = self.get_argument("email")

        # Changing username and email are trivial, just apply them and check they worked.
        ok = self.application.db.update_user(self.current_user, username=username)
        if not ok:
            self.write("Could not set username, perhaps it conflicts with an existing user.")
            return

        ok = self.application.db.update_user(self.current_user, email=email)
        if not ok:
            self.write("Could not set email, perhaps it conflicts with an existing user.")
            return

        # Check if we wanted to change our password:
        if old_password and new_password and new_password_2:
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

        self.write("Details updated successfully")