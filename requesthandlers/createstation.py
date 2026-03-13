import asyncio
import json
from datetime import datetime

import tornado

from core.utils import TEMP_STATION_NO_EVENT_COLOR, TEMP_STATION_NO_EVENT_ICON, get_default_event_start_time, \
    get_default_event_end_time, humanize_start_end, verify_recaptcha
from core.validation import validate_free_text, validate_callsign, validate_url, validate_phone, validate_email_address, \
    validate_latitude, validate_longitude
from mail.mailer import notify_admins_user_added_station, notify_owner_station_created
from requesthandlers.base import BaseHandler


class CreateStationHandler(BaseHandler):
    """Handler for the create station page (the full version where the user fills in the form, rather than the
    interstitial page where they set the type"""

    async def get(self, perm_or_temp_slug):
        """A slug is provided here, "perm" or "temp", depending on the type of station we want to create, which sets
        what's included in the form template. The form of the URL is /create/station/temp or /create/station/perm."""

        # Get data we need to include in the template. This is the list of bands and modes in case we are creating
        # a temporary station and need to set these, event and type IDs, and default start and end times for the event.
        executor = tornado.ioloop.IOLoop.current()
        all_bands = await executor.run_in_executor(None, lambda: self.application.db.get_all_bands())
        all_modes = await executor.run_in_executor(None, lambda: self.application.db.get_all_modes())
        default_start = get_default_event_start_time()
        default_end = get_default_event_end_time()
        lat = self.get_argument("lat")
        lon = self.get_argument("lon")
        event_id = 0
        if self.get_argument("event", None):
            event_id = int(self.get_argument("event", None))
        type_id = 0
        if self.get_argument("type", None):
            type_id = int(self.get_argument("type"))
        config = await executor.run_in_executor(None, lambda: self.application.db.get_config())
        enable_captcha = config.enable_captcha
        recaptcha_site_key = config.recaptcha_site_key

        # Check lat/lon were supplied and other fields are consistent with what the user could reasonably select
        if not lat or not lon:
            self.write("Required parameters not provided, user did not get to this page via normal means.")
            return
        if perm_or_temp_slug == "temp" and event_id:
            event = await executor.run_in_executor(None, lambda: self.application.db.get_event(event_id))
            if event and (not event.public or event.end_time <= datetime.now()):
                self.write(
                    "Event ID was provided for a non-existent or non-public event, or one that has already finished, user did not get to this page via normal means.")
                return
        if perm_or_temp_slug == "perm":
            perm_type = await executor.run_in_executor(None,
                                                       lambda: self.application.db.get_permanent_station_type(type_id))
            if not perm_type:
                self.write(
                    "Type ID was provided for a non-existent type, user did not get to this page via normal means.")
                return

        # Derive color/icon. We have to do this manually because we don't have a real station object yet, but for a nice
        # display for the user we want to use the real marker icon and colour at this point.
        perm_station_type = None
        event = None
        color = TEMP_STATION_NO_EVENT_COLOR
        icon = TEMP_STATION_NO_EVENT_ICON
        if perm_or_temp_slug == "perm":
            perm_station_type = await executor.run_in_executor(None,
                                                               lambda: self.application.db.get_permanent_station_type(
                                                                   type_id))
            color = perm_station_type.color
            icon = perm_station_type.icon
        elif perm_or_temp_slug == "temp":
            event = await executor.run_in_executor(None, lambda: self.application.db.get_event(event_id))
            if event:
                color = event.color
                icon = event.icon

        # Render the template. Supply the user password as well, this will be included in the form as a hidden field,
        # so we can check it again when it comes back to us in the POST.
        self.render("createstation.html", station_type=perm_or_temp_slug, latitude_degrees=lat, longitude_degrees=lon,
                    event=event, event_id=event_id, type=perm_station_type, type_id=type_id, color=color, icon=icon,
                    all_bands=all_bands, all_modes=all_modes, default_start=default_start, default_end=default_end,
                    enable_captcha=enable_captcha, recaptcha_site_key=recaptcha_site_key)

    async def post(self, perm_or_temp_slug):
        """Handle the user filling in the form and clicking Create. The "perm" or "temp" slug is provided here as well."""

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

        # Get the action we have been asked to do
        action = self.get_argument("action")

        # Check for Create action
        if action == "Create":
            # Get and validate request arguments. These could be for either a permanent or a temporary station at this
            # point, so get and validate the arguments for both if they exist.
            callsign, err_callsign = validate_callsign(self.get_argument("callsign"))
            club_name, err_club = validate_free_text(self.get_argument("club_name"), "Club Name", max_length=200)
            latitude_degrees, err_lat = validate_latitude(float(self.get_argument("latitude_degrees")))
            longitude_degrees, err_lon = validate_longitude(float(self.get_argument("longitude_degrees")))
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

            check_field_validity_errors = [err_callsign, err_club, err_notes, err_website, err_qrz, err_social,
                         err_email, err_phone, err_lat, err_lon]
            if perm_or_temp_slug == "perm":
                check_field_validity_errors.extend([err_when, err_where])
            err = next((x for x in check_field_validity_errors if x is not None), None)
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
            band_ids = []
            if self.get_argument("bands[]", None):
                band_ids = [int(x) for x in self.request.arguments["bands[]"]]
            mode_ids = []
            if self.get_argument("modes[]", None):
                mode_ids = [int(x) for x in self.request.arguments["modes[]"]]

            # Check lat/lon were supplied and other fields are consistent with what the user could reasonably select
            if not latitude_degrees or not longitude_degrees:
                self.set_status(400)
                self.write(json.dumps({
                    "message": "A location was not provided. Please <a href='/contact' class='alert-link'>contact the administrators of the site</a> for help."}))
                return
            if perm_or_temp_slug == "temp" and event_id > 0:
                event = await executor.run_in_executor(None, lambda: self.application.db.get_event(event_id))
                if not event or not event.public or event.end_time <= datetime.now():
                    self.set_status(400)
                    self.write(json.dumps({
                        "message": "Event ID was provided for a non-existent or non-public event, or one that has already finished. Please <a href='/contact' class='alert-link'>contact the administrators of the site</a> for help."}))
                    return
            if perm_or_temp_slug == "perm":
                perm_type = await executor.run_in_executor(None, lambda: self.application.db.get_permanent_station_type(
                    type_id))
                if not perm_type:
                    self.set_status(400)
                    self.write(json.dumps({
                        "message": "Type ID was provided for a non-existent type. Please <a href='/contact' class='alert-link'>contact the administrators of the site</a> for help."}))
                    return

            # Check for sensible times
            if perm_or_temp_slug == "temp" and start_time and end_time and start_time > end_time:
                self.set_status(400)
                self.write(json.dumps({
                    "message": "Your station cannot start running after it ends. Please check your time entries carefully."}))
                return

            # Check the times, bands and modes are consistent with the event, if there is one.
            if perm_or_temp_slug == "temp" and event_id > 0:
                event = await executor.run_in_executor(None,
                                                       lambda: self.application.db.get_event(event_id))
                if event:
                    if start_time < event.start_time or end_time > event.end_time:
                        self.set_status(400)
                        self.write(json.dumps({"message": event.name + " runs " + humanize_start_end(event.start_time,
                                                                                                     event.end_time) + ". Please adjust your station times to be within this period."}))
                        return
                    if any(band_id not in [band.id for band in event.bands] for band_id in band_ids):
                        self.set_status(400)
                        self.write(json.dumps({"message": event.name + " allows only the following bands: " + (
                            ", ".join([band.name for band in
                                       event.bands])) + ". Please remove any other bands you have selected for your station."}))
                        return
                    if any(mode_id not in [mode.id for mode in event.modes] for mode_id in mode_ids):
                        self.set_status(400)
                        self.write(json.dumps({"message": event.name + " allows only the following modes: " + (
                            ", ".join([mode.name for mode in
                                       event.modes])) + ". Please remove any other modes you have selected for your station."}))
                        return

            # Now create the station, taking into account its type
            new_station = None
            edit_password = None
            if perm_or_temp_slug == "perm":
                new_station_id = await executor.run_in_executor(None,
                                                                lambda: self.application.db.add_permanent_station(
                                                                    callsign=callsign,
                                                                    club_name=club_name,
                                                                    type_id=type_id,
                                                                    latitude_degrees=latitude_degrees,
                                                                    longitude_degrees=longitude_degrees,
                                                                    meeting_when=meeting_when,
                                                                    meeting_where=meeting_where,
                                                                    notes=notes,
                                                                    website_url=website_url,
                                                                    qrz_url=qrz_url,
                                                                    social_media_url=social_media_url,
                                                                    email=email,
                                                                    phone_number=phone_number))
                new_station = await executor.run_in_executor(None, lambda: self.application.db.get_permanent_station(
                    new_station_id))
                edit_password = new_station.edit_password

            elif perm_or_temp_slug == "temp":
                new_station_id = await executor.run_in_executor(None,
                                                                lambda: self.application.db.add_temporary_station(
                                                                    callsign=callsign,
                                                                    club_name=club_name,
                                                                    event_id=event_id,
                                                                    start_time=start_time,
                                                                    end_time=end_time,
                                                                    latitude_degrees=latitude_degrees,
                                                                    longitude_degrees=longitude_degrees,
                                                                    band_ids=band_ids,
                                                                    mode_ids=mode_ids,
                                                                    notes=notes,
                                                                    website_url=website_url,
                                                                    qrz_url=qrz_url,
                                                                    social_media_url=social_media_url,
                                                                    email=email,
                                                                    phone_number=phone_number))
                new_station = await executor.run_in_executor(None, lambda: self.application.db.get_temporary_station(
                    new_station_id))
                edit_password = new_station.edit_password

            if new_station:
                # Create OK. Email administrators to let the know a new station is awaiting their approval, and email
                # the station owner (if they provided an email address) to give them the edit password. If emailing was
                # successful, we include that in the redirect URL so we can customise the message the user sees. The
                # redirect URL sends them back to the view station page to show the data. We also include the edit
                # password in the GET params here, which will cause the view station page to show it to the user, and
                # they could also bookmark the URL as a way of preserving it.
                executor.run_in_executor(None,
                                         lambda: notify_admins_user_added_station(self.application.db, new_station))
                emailed = await executor.run_in_executor(None,
                                                         lambda: notify_owner_station_created(self.application.db,
                                                                                              new_station))
                self.set_status(200)
                self.write(json.dumps({"message": "Your new station has been created. Taking you there...",
                                       "redirect_url": "/view/station/" + perm_or_temp_slug + "/" + str(
                                           new_station.id) + "?edit_password=" + edit_password + "&emailed=" + str(
                                           emailed)}))
                return
            else:
                self.set_status(500)
                self.write(json.dumps(
                    {"message": "Failed to create the station. Please <a href='/contact' class='alert-link'>contact the administrators of the site</a> for help."}))
                return

        else:
            self.set_status(400)
            self.write(json.dumps({"message": "Invalid action '" + action + "'"}))
            return
