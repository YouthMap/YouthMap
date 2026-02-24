import tornado

from requesthandlers.base import BaseHandler


class AdminHandler(BaseHandler):
    """Handler for admin dashboard"""

    @tornado.web.authenticated
    async def get(self):
        # Get data we need to include in the template
        executor = tornado.ioloop.IOLoop.current()
        user = await executor.run_in_executor(None, lambda: self.application.db.get_user(self.current_user))
        insecure_user_present = await executor.run_in_executor(None,
                                                               lambda: self.application.db.is_insecure_user_present())
        perm_stations = await executor.run_in_executor(None,
                                                       lambda: self.application.db.get_all_permanent_stations())
        temp_stations = await executor.run_in_executor(None,
                                                       lambda: self.application.db.get_all_temporary_stations())
        approval_queue_length = sum(not x.approved for x in perm_stations) + sum(not x.approved for x in temp_stations)

        # Render the template
        self.render("admin.html", user=user, insecure_user_present=insecure_user_present,
                    approval_queue_length=approval_queue_length)
