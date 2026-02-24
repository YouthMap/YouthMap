import asyncio
import json
import secrets

import tornado

from core.utils import populate_derived_fields_temp_station, populate_derived_fields_perm_station, verify_recaptcha
from mail.mailer import notify_admins_user_deleted_station
from requesthandlers.base import BaseHandler


class ViewStationHandler(BaseHandler):
    """Handler for station view page"""

    async def get(self, perm_or_temp_slug, station_id_slug):
        """Two slugs are provided here. The first is "perm" or "temp", and the second is the station ID within that
        category, so e.g. the URL can be /view/station/temp/1 to view permanent station 1."""

        station_id = int(station_id_slug)

        # If "edit_password" was provided as a GET parameter, and it matches, include that in the template. This will
        # cause the password to be displayed. We use this on the first return to this page after the user has created
        # the station, to display that password and remind them to note it down. Also include the "emailed" flag which
        # lets the user know whether this password has been emailed to their registered email address or not.
        user_edit_password = self.get_argument("edit_password", "None")
        emailed = "True" == self.get_argument("emailed", None)

        # Get data we need to include in the template
        executor = tornado.ioloop.IOLoop.current()
        station = None
        edit_password_good = False
        if perm_or_temp_slug == "perm":
            station = await executor.run_in_executor(None,
                                                     lambda: self.application.db.get_permanent_station(
                                                         station_id))
            if station:
                populate_derived_fields_perm_station(station)
                edit_password_good = secrets.compare_digest(station.edit_password,
                                                            user_edit_password) if user_edit_password else False
        elif perm_or_temp_slug == "temp":
            station = await executor.run_in_executor(None,
                                                     lambda: self.application.db.get_temporary_station(
                                                         station_id))
            if station:
                populate_derived_fields_temp_station(station)
                edit_password_good = secrets.compare_digest(station.edit_password,
                                                            user_edit_password) if user_edit_password else False
        config = await executor.run_in_executor(None, lambda: self.application.db.get_config())
        enable_captcha = config.enable_captcha
        recaptcha_site_key = config.recaptcha_site_key

        # Render the template.
        if station:
            self.render("viewstation.html", type=perm_or_temp_slug, station=station,
                    user_edit_password=user_edit_password if edit_password_good else None, emailed=emailed,
                    enable_captcha=enable_captcha, recaptcha_site_key=recaptcha_site_key)
        else:
            self.write("Station not found.")

    async def post(self, perm_or_temp_slug, station_id_slug):
        """Handle the user entering an edit password and clicking Edit or Delete. This supports two 'actions' depending
         on whether the Edit or Delete button was clicked,and provides the user's edit password to compare against the
         station. Two slugs are provided here. The first is "perm" or "temp", and the second is the station ID within that
        category, so e.g. the URL can be /view/station/temp/1 to view permanent station 1."""

        # Brief delay to make spamming attacks less viable
        await asyncio.sleep(1)

        self.set_header("Content-Type", "application/json")
        executor = tornado.ioloop.IOLoop.current()

        # Check CAPTCHA if required
        config = await executor.run_in_executor(None, lambda: self.application.db.get_config())
        if config.enable_captcha:
            recaptcha_token = self.get_argument("recaptcha_token", None)
            captcha_ok = await executor.run_in_executor(None, lambda: verify_recaptcha(
                config.recaptcha_secret_key, recaptcha_token))
            if not captcha_ok:
                self.set_status(401)
                self.write(json.dumps({"message": "CAPTCHA verification failed."}))
                return

        station_id = int(station_id_slug)
        user_edit_password = self.get_argument("user_edit_password")
        edit_password_good = False

        # Check the edit password
        if perm_or_temp_slug == "perm":
            station = await executor.run_in_executor(None,
                                                     lambda: self.application.db.get_permanent_station(
                                                         station_id))
            edit_password_good = station.edit_password == user_edit_password
        elif perm_or_temp_slug == "temp":
            station = await executor.run_in_executor(None,
                                                     lambda: self.application.db.get_temporary_station(
                                                         station_id))
            edit_password_good = station.edit_password == user_edit_password

        if not edit_password_good:
            self.set_status(401)
            self.write(json.dumps({"message": "The password you provided was incorrect."}))
            return

        # Get the action we have been asked to do
        action = self.get_argument("action")

        # Check for Edit action
        if action == "Edit":
            self.set_status(200)
            self.write(json.dumps({
                "redirect_url": "/edit/station/" + perm_or_temp_slug + "/" + station_id_slug + "?edit_password=" + user_edit_password}))
            return

        # Check for Delete action
        elif action == "Delete":
            # Delete the station, but first get a copy of it so we can include its details when we email administrators.
            ok = False
            station = None
            if perm_or_temp_slug == "perm":
                station = await executor.run_in_executor(None,
                                                         lambda: self.application.db.get_permanent_station(
                                                             station_id))
                ok = await executor.run_in_executor(None,
                                                    lambda: self.application.db.delete_permanent_station(
                                                        station_id))
            elif perm_or_temp_slug == "temp":
                station = await executor.run_in_executor(None,
                                                         lambda: self.application.db.get_temporary_station(
                                                             station_id))
                ok = await executor.run_in_executor(None,
                                                    lambda: self.application.db.delete_temporary_station(
                                                        station_id))

            if ok:
                # Delete station and email administrators
                self.set_status(200)
                self.write(json.dumps({"message": "Your station has been deleted. Taking you back home...",
                                       "redirect_url": "/"}))
                if station:
                    executor.run_in_executor(None,
                                             lambda: notify_admins_user_deleted_station(self.application.db, station))
                return
            else:
                self.set_status(500)
                self.write(json.dumps({"message": "Failed to delete the station."}))
                return

        else:
            self.set_status(400)
            self.write(json.dumps({"message": "Invalid action '" + action + "'"}))
            return
