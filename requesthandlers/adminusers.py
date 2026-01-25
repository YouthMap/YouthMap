import tornado

from requesthandlers.base import BaseHandler


class AdminUsersHandler(BaseHandler):
    """Handler for admin user management page"""

    @tornado.web.authenticated
    def get(self):
        # Deny access if we are not a super-admin
        user = self.application.db.get_user(self.current_user)
        if not user.super_admin:
            self.write("You do not have permission to access this page.")
            return

        # Get data we need to include in the template
        users = self.application.db.get_all_users()

        # Render the template
        self.render("adminusers.html", users=users, current_user=user)

    def post(self):
        """Handles POST requests for user management page. This supports three 'actions' depending on whether the Update
        or Delete button was clicked for an existing user, or the Create button was clicked for a new user, and provides
        the updated data to insert back into the database. This requires the current user to have super-admin permission."""

        # Deny access if we are not a super-admin
        user = self.application.db.get_user(self.current_user)
        if not user.super_admin:
            self.write("You do not have permission to update this data.")
            return

        # Get the action we have been asked to do
        action = self.get_argument("action")

        # Check for Delete action
        if action == "Delete":
            # Get request arguments. For a Delete we only need the ID
            user_id = self.get_argument("id")

            if user_id == self.current_user:
                self.write("You can't delete yourself")
                return
            else:
                # Process the delete
                ok = self.application.db.delete_user(user_id)
                if ok:
                    # Delete OK, just reload the page which will have the new data in it
                    self.redirect("/admin/users")
                else:
                    self.write("Failed to delete user")

        # Check for Update action
        elif action == "Update":
            # Get request arguments. For an update we need ID plus username and email; optionally also password and
            # super_admin. (The POST only contains the super_admin flag if the checkbox is ticked, otherwise it is not
            # sent.)
            user_id = self.get_argument("id")
            username = self.get_argument("username")
            password = self.get_argument("password", None)
            email = self.get_argument("email")
            super_admin = True if self.get_argument("super_admin", None) else False

            # Ignore requests that look like they are removing your own super-admin status. In the HTML, the super_admin
            # checkbox for the current user is shown checked, but disabled. This has the effect that the super_admin
            # flag will not be POSTed, even though it is checked. This looks the same as having super_admin unchecked.
            # Since it's a bad idea for the current user to remove that flag from themselves, we ignore it.
            if user_id == self.current_user:
                super_admin = True

            # Password is optional, so if we got a blank string, set the value to None so that we don't update that
            # aspect of the user.
            password = password if password != "" else None

            # Process the update
            ok = self.application.db.update_user(user_id, username=username, password=password, email=email,
                                                 super_admin=super_admin)
            if ok:
                # Update OK, just reload the page which will have the new data in it
                self.redirect("/admin/users")
            else:
                self.write("Failed to update user")

        # Check for Create action
        elif action == "Create":
            # Get request arguments. For a create we need username, password, email and optionally super_admin (the POST
            # only contains the super_admin flag if the checkbox is ticked, otherwise it is not sent.)
            username = self.get_argument("username")
            password = self.get_argument("password")
            email = self.get_argument("email")
            super_admin = True if self.get_argument("super_admin", None) else False

            # Process the update
            ok = self.application.db.add_user(username=username, password=password, email=email,
                                                 super_admin=super_admin)
            if ok:
                # Update OK, just reload the page which will have the new data in it
                self.redirect("/admin/users")
            else:
                self.write("Failed to add user")
        else:
            self.write("Invalid action '" + action + "'")
