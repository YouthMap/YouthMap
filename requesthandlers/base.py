import tornado


class BaseHandler(tornado.web.RequestHandler):
    """Request handler superclass providing common functions"""

    def get_current_user(self):
        """Get the current user by verifying the cookie token"""

        session_token = self.get_secure_cookie("session_token")
        if not session_token:
            return None

        return self.application.db.verify_user_session_token(session_token.decode('utf-8'))

    def render(self, template_name, **kwargs):
        """Override the render function, provides a common place to include stuff like base URL and current path into
        all templates"""

        config = self.application.db.get_config()
        kwargs.setdefault('baseurl', config.base_url if config else '')
        kwargs.setdefault('current_path', self.request.path)
        super().render(template_name, **kwargs)
