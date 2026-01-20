from requesthandlers.base import BaseHandler


class LoginHandler(BaseHandler):
    """Handler for login page, includes POSTing username and password as well as rendering the HTML"""

    def get(self):
        if self.current_user:
            self.redirect("/admin")
            return

        self.write('''
            <html>
            <body>
                <h1>Admin Login</h1>
                <form method="post">
                    <input type="text" name="username" placeholder="Username" required><br>
                    <input type="password" name="password" placeholder="Password" required><br>
                    <input type="submit" value="Login">
                </form>
            </body>
            </html>
        ''')

    def post(self):
        username = self.get_argument("username")
        password = self.get_argument("password")

        admin_id = self.application.db.verify_admin(username, password)

        if admin_id:
            session_token = self.application.db.create_session(admin_id)
            self.set_secure_cookie("session_token", session_token)
            self.redirect("/admin")
        else:
            self.write("Invalid credentials")
