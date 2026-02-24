import json

import tornado

from core.utils import generate_password
from core.validation import validate_free_text, validate_email_address
from mail.mailer import notify_user_account_created
from requesthandlers.base import BaseHandler


class AdminUserHandler(BaseHandler):
    """Handler for user details page, includes POSTing the new details as well as rendering the HTML. This does double
    duty not just for the user to update their own details (e.g. reset their password) but also for super-admins to
    create, update and delete other user accounts."""

    @tornado.web.authenticated
    async def get(self, slug=None):
        """The slug here is the user ID, so e.g. the URL can be /admin/user/1 to edit user 1. A special slug of 'new' is
         also allowed, which sets up the form to create a user rather than to edit one."""

        user_id = int(slug) if slug != "new" else self.current_user
        creating_new = (slug == "new")

        # Get data we need to include in the template
        executor = tornado.ioloop.IOLoop.current()
        user = None
        is_me = False
        if not creating_new:
            user = await executor.run_in_executor(None, lambda: self.application.db.get_user(user_id))
            is_me = user_id == self.current_user
        current_user = await executor.run_in_executor(None, lambda: self.application.db.get_user(
            self.current_user))

        # Bail out if the user is a non-super-admin and is editing a user that's not their own (or trying to create a
        # new one)
        if not current_user.super_admin and (creating_new or not is_me):
            self.write("You are not permitted to use this page for anything other than editing your own user account.")
            return

        # Check if mail is enabled, if not we need to set the user's password manually on creation
        config = await executor.run_in_executor(None, lambda: self.application.db.get_config())
        mail_enabled = config.enable_mail

        # Render the template
        if user or creating_new:
            self.render("adminuser.html", user=user, current_user=current_user, creating_new=creating_new,
                        mail_enabled=mail_enabled)
        else:
            self.write("User not found.")

    @tornado.web.authenticated
    async def post(self, slug):
        """Handles POST requests for user editing page. This supports three 'actions' depending on whether the Update
        or Delete button was clicked for an existing user, or the Create button was clicked for a new user, and provides
        the updated data to insert back into the database. This requires the current user to have super-admin permission.
        The slug here is the user ID, so e.g. the URL can be /admin/user/1 to edit user 1. A special slug of 'new' is
        also allowed, which sets up the form to create a user rather than to edit one."""

        self.set_header("Content-Type", "application/json")
        executor = tornado.ioloop.IOLoop.current()

        # Get the action we have been asked to do
        action = self.get_argument("action")

        # Check which user we are, and which user we are editing
        current_user = await executor.run_in_executor(None, lambda: self.application.db.get_user(
            self.current_user))
        editing_user_id = 0
        if slug != "new":
            editing_user_id = current_user.id if (slug == "me") else int(slug)
        editing_self = editing_user_id == current_user.id

        # Bail out if the user is a non-super-admin and is editing a user that's not their own (or trying to create a
        # new one)
        if not current_user.super_admin:
            if slug == "new" or action == "Create":
                self.set_status(401)
                self.write(json.dumps({"message": "You are not permitted to create user accounts."}))
                return
            elif not editing_self:
                self.set_status(401)
                self.write(json.dumps({"message": "You are not permitted to update a user account other than your own."}))
                return

        # Check for Delete action
        if action == "Delete":
            # Process the delete action
            ok = await executor.run_in_executor(None, lambda: self.application.db.delete_user(
                editing_user_id))
            if ok:
                # Delete OK. If you were deleting yourself, go back to the home page, otherwise it was an admin
                # deleting somebody else, so go back to the user management page.
                if editing_self:
                    self.set_status(200)
                    self.write(json.dumps(
                        {"message": "Your account has been deleted. Returning you to the home page...",
                         "redirect_url": "/"}))
                    return
                else:
                    self.set_status(200)
                    self.write(json.dumps(
                        {"message": "User deleted. Returning you to the user list...", "redirect_url": "/admin/users"}))
                    return
            else:
                self.set_status(500)
                self.write(
                    json.dumps({"message": "Failed to delete the user. Please check the logs for more details."}))
                return

        # Check for Update action
        elif action == "Update":
            # Get and validate request arguments. For an update we need username and email; optionally also password
            # and super_admin.
            username, err_username = validate_free_text(self.get_argument("username"), "username", max_length=100)
            email, err_email = validate_email_address(self.get_argument("email"))

            err = next((x for x in [err_username, err_email] if x is not None), None)
            if err:
                self.set_status(400)
                self.write(json.dumps({"message": err}))
                return

            # Get request arguments that don't need separate validation
            password = self.get_argument("password", None)
            super_admin = True if self.get_argument("super_admin", None) else False

            # Check for a change that would change the current user's own super-admin status. Adding it when they don't
            # have it is privilege escalation, and removing it when they have it could leave the site with no
            # super-admins, so bail out.
            if editing_self and ((current_user.super_admin and not super_admin)
                          or (not current_user.super_admin and super_admin)):
                self.set_status(401)
                self.write(json.dumps({"message": "Changing your own super-admin status is not allowed."}))
                return

            # Catch a uniqueness violation before it happens, so we can explicitly warn the user about this
            all_users = await executor.run_in_executor(None,
                                                       lambda: self.application.db.get_all_users())
            other_users = [u for u in all_users if u.id != editing_user_id]
            if any(u.username.lower() == username.lower() for u in other_users):
                self.set_status(400)
                self.write(json.dumps({
                    "message": "Another user is already called '" + username + "'. User names must be unique, and are not case sensitive."}))
                return

            # Process the update
            ok = await executor.run_in_executor(None, lambda: self.application.db.update_user(
                editing_user_id, username=username, password=password, email=email,
                super_admin=super_admin))
            if ok:
                # Update OK
                self.set_status(200)
                self.write(json.dumps(
                    {"message": "User updated. Returning you to the user list...", "redirect_url": "/admin/users"}))
                return
            else:
                self.set_status(500)
                self.write(
                    json.dumps({"message": "Failed to update the user. Please check the logs for more details."}))
                return

        # Check for Create action
        elif action == "Create":
            # Get and validate request arguments.
            username, err_username = validate_free_text(self.get_argument("username"), "username", max_length=100)
            email, err_email = validate_email_address(self.get_argument("email"))

            err = next((x for x in [err_username, err_email] if x is not None), None)
            if err:
                self.set_status(400)
                self.write(json.dumps({"message": err}))
                return

            # Get request arguments that don't need separate validation
            # Use a provided password or fall back to an auto-generated one
            password = self.get_argument("password", generate_password())
            super_admin = True if self.get_argument("super_admin", None) else False

            # Catch a uniqueness violation before it happens, so we can explicitly warn the user about this
            other_users = await executor.run_in_executor(None,
                                                         lambda: self.application.db.get_all_users())
            if any(u.username.lower() == username.lower() for u in other_users):
                self.set_status(400)
                self.write(json.dumps({
                    "message": "Another user is already called '" + username + "'. User names must be unique, and are not case sensitive."}))
                return

            # Process the create action
            new_user_id = await executor.run_in_executor(None, lambda: self.application.db.add_user(
                username=username, password=password, email=email,
                super_admin=super_admin))
            if new_user_id:
                # Create OK. Email the user their details.
                executor.run_in_executor(None, lambda: notify_user_account_created(self.application.db, email, username,
                                                                                   password))
                self.set_status(200)
                self.write(json.dumps(
                    {"message": "User created. Returning you to the user list...", "redirect_url": "/admin/users"}))
                return
            else:
                self.set_status(500)
                self.write(
                    json.dumps({"message": "Failed to create the user. Please check the logs for more details."}))
                return

        else:
            self.set_status(400)
            self.write(json.dumps({"message": "Invalid action '" + action + "'"}))
            return
