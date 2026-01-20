import tornado

from requesthandlers.base import BaseHandler


class AdminHandler(BaseHandler):
    """Handler for admin dashboard"""

    @tornado.web.authenticated
    def get(self):
        self.write(f'''
            <html>
            <body>
                <h1>Admin Dashboard</h1>
                <p>Admin controls here</p>
                <a href="/logout">Logout</a>
            </body>
            </html>
        ''')
