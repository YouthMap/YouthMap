import tornado

from requesthandlers.base import BaseHandler


class AdminHandler(BaseHandler):
    """Handler for admin dashboard"""

    @tornado.web.authenticated
    def get(self):
        username = self.application.db.get_user(self.current_user).username

        self.write(f'''
            <html>
            <body>
                <h1>Admin Dashboard</h1>
                <p>Hello {username}</p>
                <p>Admin controls here</p>
                <p><a href="/changepassword">Change password</a></p>
                <p><a href="/logout">Logout</a></p>
            </body>
            </html>
        ''')
