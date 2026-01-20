from requesthandlers.base import BaseHandler


class MapHandler(BaseHandler):
    """Handler for the main map page"""

    def get(self):
        self.write(f'''
            <html>
            <body>
                <h1>Youth Map</h1>
                <p>Map here</p>
                <a href="/login">Admin login</a>
            </body>
            </html>
        ''')
