import tornado

from requesthandlers.base import BaseHandler


class AdminUserHandler(BaseHandler):
    """Handler for user details page, includes POSTing the new details as well as rendering the HTML. This does double
    duty not just for the user to update their own details (e.g. reset their password) but also for super-admins to
    create, update and delete other user accounts."""

    @tornado.web.authenticated
    def get(self, slug=None):
        """The slug here is the user ID, so e.g. the URL can be /admin/user/1 to edit user 1. A special slug of 'new' is
         also allowed, which sets up the form to create a user rather than to edit one."""

        user_id = int(slug) if slug != "new" else self.current_user
        creating_new = (slug == "new")

        # Get data we need to include in the template
        user = None
        is_me = False
        if not creating_new:
            user = self.application.db.get_user(user_id)
            is_me = user_id == self.current_user
        current_user = self.application.db.get_user(self.current_user)

        # Bail out if the user is a non-super-admin and is editing a user that's not their own (or trying to create a
        # new one)
        if not current_user.super_admin and (creating_new or not is_me):
            self.write("You are not permitted to use this page for anything other than editing your own user account.")
            return

        # Render the template
        self.render("adminuser.html", user=user, current_user=current_user, creating_new=creating_new)

    @tornado.web.authenticated
    def post(self, slug):
        """Handles POST requests for user editing page. This supports three 'actions' depending on whether the Update
        or Delete button was clicked for an existing user, or the Create button was clicked for a new user, and provides
        the updated data to insert back into the database. This requires the current user to have super-admin permission.
        The slug here is the user ID, so e.g. the URL can be /admin/user/1 to edit user 1. A special slug of 'new' is
        also allowed, which sets up the form to create a user rather than to edit one."""

        # Bail out if the user is a non-super-admin and is editing a user that's not their own (or trying to create a
        # new one)
        user_id = int(slug) if (slug != "me" and slug != "new") else self.current_user
        is_me = user_id == self.current_user
        current_user = self.application.db.get_user(self.current_user)
        if not is_me and not current_user.super_admin:
            self.write("You are not permitted to update a user account other than your own.")
            return

        # Get the action we have been asked to do
        action = self.get_argument("action")

        # Check for Delete action
        if action == "Delete":
            # Process the delete action
            ok = self.application.db.delete_user(user_id)
            if ok:
                # Delete OK. If you were deleting yourself, go back to the home page, otherwise it was an admin
                # deleting somebody else, so go back to the user management page.
                if is_me:
                    self.redirect("/")
                else:
                    self.redirect("/admin/users")
            else:
                self.write("Failed to delete user")
                return

        # Check for Update action
        elif action == "Update":
            # Get request arguments. For an update we need username and email; optionally also password and
            # super_admin. (The POST only contains the super_admin flag if the checkbox is ticked, otherwise it is not
            # sent.)
            username = self.get_argument("username")
            password = self.get_argument("password", None)
            email = self.get_argument("email")
            super_admin = True if self.get_argument("super_admin", None) else False

            # Check for a change that would change the current user's own super-admin status. Adding it when they don't
            # have it is priviledge escalation, and removing it when they have it could leave the site with no
            # super-admins, so bail out.
            if is_me and ((current_user.super_admin and not super_admin)
                    or (not current_user.super_admin and super_admin)):
                self.write("Changing your own super-admin status is not allowed.")
                return

            # Password is optional, so if we got a blank string, set the value to None so that we don't update that
            # aspect of the user.
            password = password if password != "" else None

            # Process the update
            ok = self.application.db.update_user(user_id, username=username, password=password, email=email,
                                                 super_admin=super_admin)
            if ok:
                # Update OK, just reload the page which will have the new data in it
                self.redirect("/admin/user/" + slug)
            else:
                self.write("Failed to update user")
                return

        # Check for Create action
        elif action == "Create":
            # Get request arguments. For a create action we need username, password, email and optionally super_admin
            # (the POST only contains the super_admin flag if the checkbox is ticked, otherwise it is not sent.)
            username = self.get_argument("username")
            password = self.get_argument("password")
            email = self.get_argument("email")
            super_admin = True if self.get_argument("super_admin", None) else False

            # Process the create action
            new_user_id = self.application.db.add_user(username=username, password=password, email=email,
                                              super_admin=super_admin)
            if new_user_id:
                # Create OK, go back to the user management page which will have the new data in it
                self.redirect("/admin/users/")
            else:
                self.write("Failed to add user")
                return
        else:
            self.write("Invalid action '" + action + "'")










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
