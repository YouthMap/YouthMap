import tornado


class BaseHandler(tornado.web.RequestHandler):
    """Request handler superclass providing common functions"""

    def get_current_user(self):
        session_token = self.get_secure_cookie("session_token")
        if not session_token:
            return None

        admin_id = self.application.db.verify_user_session_token(session_token.decode('utf-8'))
        return admin_id
