import tornado

from requesthandlers.base import BaseHandler


# noinspection PyUnresolvedReferences
class AdminHandler(BaseHandler):
    """Handler for admin dashboard"""

    @tornado.web.authenticated
    def get(self):
        # Get data we need to include in the template
        user = self.application.db.get_user(self.current_user)
        insecure_user_present = self.application.db.is_insecure_user_present()
        approval_queue_length = sum(not x.approved for x in self.application.db.get_all_permanent_stations()) + sum(
            not x.approved for x in self.application.db.get_all_temporary_stations())

        # Render the template
        self.render("admin.html", user=user, insecure_user_present=insecure_user_present,
                    approval_queue_length=approval_queue_length)
