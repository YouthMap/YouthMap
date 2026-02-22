import json
from datetime import datetime
from time import sleep

from core.utils import populate_derived_fields_temp_station, populate_derived_fields_perm_station, verify_recaptcha
from core.validation import validate_callsign, validate_free_text, validate_phone, validate_url, \
    validate_email_address
from mail.mailer import notify_admins_user_updated_station, notify_admins_user_deleted_station
from requesthandlers.base import BaseHandler


class EditStationHandler(BaseHandler):
    """Handler for station edit page"""

    def get(self, perm_or_temp_slug, station_id_slug):
        """Two slugs are provided here. The first is "perm" or "temp", and the second is the station ID within that
        category, so e.g. the URL can be /edit/station/temp/1 to edit permanent station 1."""

        station_id = int(station_id_slug)

        # Get data we need to include in the template
        station = None
        station_event = None
        if perm_or_temp_slug == "perm":
            station = self.application.db.get_permanent_station(station_id)
            populate_derived_fields_perm_station(station)
        elif perm_or_temp_slug == "temp":
            station = self.application.db.get_temporary_station(station_id)
            populate_derived_fields_temp_station(station)
            station_event = self.application.db.get_event(station.event_id)
        all_bands = self.application.db.get_all_bands()
        all_modes = self.application.db.get_all_modes()
        all_perm_station_types = self.application.db.get_all_permanent_station_types()
        enable_captcha = self.application.db.get_config().enable_captcha
        recaptcha_site_key = self.application.db.get_config().recaptcha_site_key

        # Check edit password is supplied and correct
        user_edit_password = self.get_argument("edit_password")
        edit_password_good = station.edit_password == user_edit_password
        if not edit_password_good:
            self.write("Password incorrect")
            return

        # Render the template. Supply the user password as well, this will be included in the form as a hidden field,
        # so we can check it again when it comes back to us in the POST.
        if station:
            self.render("editstation.html", station_type=perm_or_temp_slug, station=station,
                        all_perm_station_types=all_perm_station_types, station_event=station_event,
                        all_bands=all_bands, all_modes=all_modes, user_edit_password=user_edit_password,
                        enable_captcha=enable_captcha, recaptcha_site_key=recaptcha_site_key)
        else:
            self.write("Station not found.")

    def post(self, perm_or_temp_slug, station_id_slug):
        """Handle the user filling in the form and clicking Update or Delete. This supports two 'actions' depending
        on whether the Update or Delete button was clicked. Two slugs are provided here. The first is "perm" or "temp",
        and the second is the station ID within that category, so e.g. the URL can be /edit/station/temp/1 to edit
        permanent station 1."""

        # Brief delay to make spamming attacks less viable
        sleep(1)

        self.set_header("Content-Type", "application/json")

        # Check CAPTCHA if required
        if self.application.db.get_config().enable_captcha:
            recaptcha_token = self.get_argument("recaptcha_token", None)
            if not verify_recaptcha(self.application.db.get_config().recaptcha_secret_key, recaptcha_token):
                self.set_status(401)
                self.write(json.dumps({"message": "CAPTCHA verification failed."}))
                return

        station_id = int(station_id_slug)
        user_edit_password = self.get_argument("user_edit_password")
        edit_password_good = False

        # Check the edit password
        if perm_or_temp_slug == "perm":
            station = self.application.db.get_permanent_station(station_id)
            edit_password_good = station.edit_password == user_edit_password
        elif perm_or_temp_slug == "temp":
            station = self.application.db.get_temporary_station(station_id)
            edit_password_good = station.edit_password == user_edit_password

        if not edit_password_good:
            self.set_status(401)
            self.write(json.dumps({"message": "The password you provided was incorrect."}))
            return

        # Get the action we have been asked to do
        action = self.get_argument("action")

        # Check for Edit action
        if action == "Update":
            # Get and validate request arguments. These could be for either a permanent or a temporary station at this
            # point, so get and validate the arguments for both if they exist.
            callsign, err_callsign = validate_callsign(self.get_argument("callsign"))
            club_name, err_club = validate_free_text(self.get_argument("club_name"), "Club Name", max_length=200)
            notes, err_notes = validate_free_text(self.get_argument("notes", "") or "", "Notes", max_length=5000)
            meeting_when, err_when = validate_free_text(self.get_argument("meeting_when", "") or "", "Meeting times",
                                                        max_length=1000)
            meeting_where, err_where = validate_free_text(self.get_argument("meeting_where", "") or "", "Meeting place",
                                                          max_length=1000)
            website_url, err_website = validate_url(self.get_argument("website_url", "") or "", "Website")
            qrz_url, err_qrz = validate_url(self.get_argument("qrz_url", "") or "", "QRZ page")
            social_media_url, err_social = validate_url(self.get_argument("social_media_url", "") or "",
                                                        "Social media")
            email, err_email = validate_email_address(self.get_argument("email", "") or "")
            phone_number, err_phone = validate_phone(self.get_argument("phone_number", "") or "")

            err = next((x for x in
                        [err_callsign, err_club, err_notes, err_when, err_where, err_website, err_qrz, err_social,
                         err_email, err_phone] if x is not None), None)
            if err:
                self.set_status(400)
                self.write(json.dumps({"message": err}))
                return

            # Get request arguments that don't need separate validation
            event_id = 0
            if self.get_argument("event", None):
                event_id = int(self.get_argument("event", None))
            type_id = 0
            if self.get_argument("type", None):
                type_id = int(self.get_argument("type"))
            start_time = None
            if self.get_argument("start_time", None):
                start_time = datetime.strptime(self.get_argument("start_time"), "%Y-%m-%dT%H:%M")
            end_time = None
            if self.get_argument("end_time", None):
                end_time = datetime.strptime(self.get_argument("end_time"), "%Y-%m-%dT%H:%M")
            latitude_degrees = float(self.get_argument("latitude_degrees"))
            longitude_degrees = float(self.get_argument("longitude_degrees"))
            band_ids = []
            if self.get_argument("bands[]", None):
                band_ids = [int(x) for x in self.request.arguments["bands[]"]]
            mode_ids = []
            if self.get_argument("modes[]", None):
                mode_ids = [int(x) for x in self.request.arguments["modes[]"]]

            # Now update the station, taking into account its type
            ok = False
            station = None
            if perm_or_temp_slug == "perm":
                ok = self.application.db.update_permanent_station(station_id, callsign=callsign, club_name=club_name,
                                                                  type_id=type_id,
                                                                  latitude_degrees=latitude_degrees,
                                                                  longitude_degrees=longitude_degrees,
                                                                  meeting_when=meeting_when,
                                                                  meeting_where=meeting_where,
                                                                  notes=notes, website_url=website_url, qrz_url=qrz_url,
                                                                  social_media_url=social_media_url, email=email,
                                                                  phone_number=phone_number)
                station = self.application.db.get_permanent_station(station_id)

            elif perm_or_temp_slug == "temp":
                ok = self.application.db.update_temporary_station(station_id, callsign=callsign, club_name=club_name,
                                                                  event_id=event_id, start_time=start_time,
                                                                  end_time=end_time,
                                                                  latitude_degrees=latitude_degrees,
                                                                  longitude_degrees=longitude_degrees,
                                                                  band_ids=band_ids,
                                                                  mode_ids=mode_ids,
                                                                  notes=notes, website_url=website_url, qrz_url=qrz_url,
                                                                  social_media_url=social_media_url, email=email,
                                                                  phone_number=phone_number)
                station = self.application.db.get_temporary_station(station_id)

            if ok:
                # Update OK, go back to the view station page to show new data. Also email the admins to let them know.
                self.set_status(200)
                self.write(json.dumps({"message": "Your station has been updated. Taking you back there...",
                                       "redirect_url": "/view/station/" + perm_or_temp_slug + "/" + station_id_slug}))
                notify_admins_user_updated_station(self.application.db, station)
                return
            else:
                self.set_status(500)
                self.write(json.dumps(
                    {"message": "Failed to update the station. Please contact the administrators (TODO) for help."}))
                return

        # Check for Delete action
        elif action == "Delete":
            # Delete the station, but first get a copy of it so we can include its details when we email administrators.
            ok = False
            station = None
            if perm_or_temp_slug == "perm":
                station = self.application.db.get_permanent_station(station_id)
                ok = self.application.db.delete_permanent_station(station_id)
            elif perm_or_temp_slug == "temp":
                station = self.application.db.get_temporary_station(station_id)
                ok = self.application.db.delete_temporary_station(station_id)

            if ok:
                # Delete station and email administrators
                self.set_status(200)
                self.write(json.dumps({"message": "Your station has been deleted. Taking you back home...",
                                       "redirect_url": "/"}))
                if station:
                    notify_admins_user_deleted_station(self.application.db, station)
                return
            else:
                self.set_status(500)
                self.write(json.dumps(
                    {"message": "Failed to delete the station. Please contact the administrators (TODO) for help."}))
                return

        else:
            self.set_status(400)
            self.write(json.dumps({"message": "Invalid action '" + action + "'"}))
            return
