import tornado

from requesthandlers.base import BaseHandler


class ChangePasswordHandler(BaseHandler):
    """Handler for change password page, includes POSTing the passwords as well as rendering the HTML"""

    @tornado.web.authenticated
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        username = self.application.db.get_user(self.current_user).username

        self.write(f'''
            <html>
            <body>
                <h1>Change password</h1>
                <p>Changing password for {username}</p>
                <form method="post">
                    <input type="password" name="old_password" placeholder="Old Password" required><br>
                    <input type="password" name="new_password" placeholder="New Password" required><br>
                    <input type="password" name="new_password_2" placeholder="New Password (again)" required><br>
                    <input type="submit" value="Change password">
                </form>
            </body>
            </html>
        ''')

    def post(self):
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

        # OK to proceed
        self.application.db.update_user(self.current_user, password=new_password)
        self.write("Password changed")