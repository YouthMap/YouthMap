import json
from datetime import datetime

import tornado

from core.utils import get_default_event_end_time, get_default_event_start_time, populate_derived_fields_temp_station, \
    humanize_start_end, to_json_sanitized
from core.validation import validate_callsign, validate_free_text, validate_url, validate_phone, validate_email_address, \
    validate_latitude, validate_longitude
from mail.mailer import notify_owner_station_approved, notify_owner_station_approval_revoked, \
    notify_owner_station_deleted
from requesthandlers.base import BaseHandler


class AdminStationTempHandler(BaseHandler):
    """Handler for admin temporary station editing page"""

    @tornado.web.authenticated
    def get(self, slug):
        """The slug here is the temporary station ID, so e.g. the URL can be /admin/station/temp/1 to edit temporary
        station 1. A special slug of 'new' is also allowed, which sets up the form to create a temporary station rather
        than to edit one."""

        station_id = int(slug) if slug != "new" else None
        creating_new = (slug == "new")

        # Get data we need to include in the template
        station = self.application.db.get_temporary_station(station_id) if not creating_new else None
        if station:
            populate_derived_fields_temp_station(station)
        all_bands = self.application.db.get_all_bands()
        all_modes = self.application.db.get_all_modes()
        all_events = self.application.db.get_all_events()
        default_start = get_default_event_start_time()
        default_end = get_default_event_end_time()
        # Include a JSON version of all events. This allows us to pull out the start/end times, notes template, bands
        # and modes from the event in real time via JS when the user selects an event from the drop-down.
        all_events_json = to_json_sanitized(self.get_events_js())

        # Render the template
        if station or creating_new:
            self.render("adminstationtemp.html", station=station, creating_new=creating_new, all_events=all_events,
                        all_bands=all_bands, all_modes=all_modes, default_start=default_start, default_end=default_end,
                        all_events_json=all_events_json)
        else:
            self.write("Station not found.")

    @tornado.web.authenticated
    def post(self, slug):
        """Handles POST requests for temporary station editing page. This supports three 'actions' depending on whether
        the Update or Delete button was clicked for an existing station, or the Create button was clicked for a new
        station, and provides the updated data to insert back into the database. The slug here is the temporary station
        ID, so e.g. the URL can be /admin/station/temp/1 to edit temporary station 1. A special slug of 'new' is also
        allowed, which sets up the form to create a temporary station rather than to edit one."""

        self.set_header("Content-Type", "application/json")

        station_id = int(slug) if slug != "new" else None

        # Get the action we have been asked to do
        action = self.get_argument("action")

        # Check for Delete action
        if action == "Delete":
            # Process the delete action
            station = self.application.db.get_temporary_station(station_id)
            ok = self.application.db.delete_temporary_station(station_id)
            if ok:
                # Delete OK
                self.set_status(200)
                self.write(json.dumps({"message": "Station deleted. Returning you to the stations list...",
                                       "redirect_url": "/admin/stations"}))

                # Email the owner to let them know
                notify_owner_station_deleted(self.application.db, station)
                return
            else:
                self.set_status(500)
                self.write(
                    json.dumps({"message": "Failed to delete the station. Please check the logs for more details."}))
                return

        # Check for Update action
        elif action == "Update":
            # Get and validate request arguments
            callsign, err_callsign = validate_callsign(self.get_argument("callsign"))
            club_name, err_club = validate_free_text(self.get_argument("club_name"), "Club Name", max_length=200)
            latitude_degrees, err_lat = validate_latitude(float(self.get_argument("latitude_degrees")))
            longitude_degrees, err_lon = validate_longitude(float(self.get_argument("longitude_degrees")))
            notes, err_notes = validate_free_text(self.get_argument("notes", "") or "", "Notes", max_length=5000)
            website_url, err_website = validate_url(self.get_argument("website_url", "") or "", "Website")
            qrz_url, err_qrz = validate_url(self.get_argument("qrz_url", "") or "", "QRZ page")
            social_media_url, err_social = validate_url(self.get_argument("social_media_url", "") or "",
                                                        "Social media")
            email, err_email = validate_email_address(self.get_argument("email", "") or "")
            phone_number, err_phone = validate_phone(self.get_argument("phone_number", "") or "")
            edit_password, err_pw = validate_free_text(self.get_argument("edit_password"), "edit password",
                                                       max_length=200)

            err = next((x for x in
                        [err_callsign, err_club, err_notes, err_website, err_qrz, err_social, err_email, err_phone,
                         err_pw, err_lat, err_lon] if x is not None), None)
            if err:
                self.set_status(400)
                self.write(json.dumps({"message": err}))
                return

            # Get request arguments that don't need separate validation
            event_id = 0
            if self.get_argument("event", None):
                event_id = int(self.get_argument("event", None))
            start_time = datetime.strptime(self.get_argument("start_time"), "%Y-%m-%dT%H:%M")
            end_time = datetime.strptime(self.get_argument("end_time"), "%Y-%m-%dT%H:%M")
            band_ids = []
            if self.get_argument("bands[]", None):
                band_ids = [int(x) for x in self.request.arguments["bands[]"]]
            mode_ids = []
            if self.get_argument("modes[]", None):
                mode_ids = [int(x) for x in self.request.arguments["modes[]"]]
            rsgb_attending = True if self.get_argument("rsgb_attending", None) else False
            approved = True if self.get_argument("approved", None) else False

            # Check for sensible times
            if start_time > end_time:
                self.set_status(400)
                self.write(json.dumps({
                    "message": "Your station cannot start running after it ends. Please check your time entries carefully."}))
                return

            # Check the times, bands and modes are consistent with the event, if there is one.
            if event_id > 0:
                event = self.application.db.get_event(event_id)
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

            # Check for approval changes to email the owner
            station = self.application.db.get_temporary_station(station_id)
            approval_happened = approved and not station.approved
            approval_revoked = station.approved and not approved

            # Process the update
            ok = self.application.db.update_temporary_station(station_id, callsign=callsign, club_name=club_name,
                                                              event_id=event_id, start_time=start_time,
                                                              end_time=end_time,
                                                              latitude_degrees=latitude_degrees,
                                                              longitude_degrees=longitude_degrees, band_ids=band_ids,
                                                              mode_ids=mode_ids,
                                                              notes=notes, website_url=website_url, qrz_url=qrz_url,
                                                              social_media_url=social_media_url, email=email,
                                                              phone_number=phone_number, rsgb_attending=rsgb_attending,
                                                              approved=approved,
                                                              edit_password=edit_password)
            if ok:
                # Update OK
                self.set_status(200)
                self.write(json.dumps({"message": "Station updated. Returning you to the stations list...",
                                       "redirect_url": "/admin/stations"}))

                # Email the station owner if the approval status changed.
                if approval_happened:
                    notify_owner_station_approved(self.application.db, station)
                elif approval_revoked:
                    notify_owner_station_approval_revoked(self.application.db, station)
                return
            else:
                self.set_status(500)
                self.write(
                    json.dumps({"message": "Failed to update the station. Please check the logs for more details."}))
                return

        # Check for Create action
        elif action == "Create":
            # Get and validate request arguments
            callsign, err_callsign = validate_callsign(self.get_argument("callsign"))
            club_name, err_club = validate_free_text(self.get_argument("club_name"), "Club Name", max_length=200)
            latitude_degrees, err_lat = validate_latitude(float(self.get_argument("latitude_degrees")))
            longitude_degrees, err_lon = validate_longitude(float(self.get_argument("longitude_degrees")))
            notes, err_notes = validate_free_text(self.get_argument("notes", "") or "", "Notes", max_length=5000)
            website_url, err_website = validate_url(self.get_argument("website_url", "") or "", "Website")
            qrz_url, err_qrz = validate_url(self.get_argument("qrz_url", "") or "", "QRZ page")
            social_media_url, err_social = validate_url(self.get_argument("social_media_url", "") or "",
                                                        "Social media")
            email, err_email = validate_email_address(self.get_argument("email", "") or "")
            phone_number, err_phone = validate_phone(self.get_argument("phone_number", "") or "")

            err = next((x for x in
                        [err_callsign, err_club, err_notes, err_website, err_qrz, err_social, err_email, err_phone,
                         err_lat, err_lon] if x is not None), None)
            if err:
                self.set_status(400)
                self.write(json.dumps({"message": err}))
                return

            # Get request arguments that don't need separate validation
            event_id = 0
            if self.get_argument("event", None):
                event_id = int(self.get_argument("event", None))
            start_time = datetime.strptime(self.get_argument("start_time"), "%Y-%m-%dT%H:%M")
            end_time = datetime.strptime(self.get_argument("end_time"), "%Y-%m-%dT%H:%M")
            band_ids = []
            if self.get_argument("bands[]", None):
                band_ids = [int(x) for x in self.request.arguments["bands[]"]]
            mode_ids = []
            if self.get_argument("modes[]", None):
                mode_ids = [int(x) for x in self.request.arguments["modes[]"]]
            rsgb_attending = True if self.get_argument("rsgb_attending", None) else False
            approved = True if self.get_argument("approved", None) else False

            # Check for sensible times
            if start_time > end_time:
                self.set_status(400)
                self.write(json.dumps({
                    "message": "Your station cannot start running after it ends. Please check your time entries carefully."}))
                return

            # Check the times, bands and modes are consistent with the event, if there is one.
            if event_id > 0:
                event = self.application.db.get_event(event_id)
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

            # Process the create action
            new_station_id = self.application.db.add_temporary_station(callsign=callsign, club_name=club_name,
                                                                       event_id=event_id, start_time=start_time,
                                                                       end_time=end_time,
                                                                       latitude_degrees=latitude_degrees,
                                                                       longitude_degrees=longitude_degrees,
                                                                       band_ids=band_ids,
                                                                       mode_ids=mode_ids,
                                                                       notes=notes, website_url=website_url,
                                                                       qrz_url=qrz_url,
                                                                       social_media_url=social_media_url, email=email,
                                                                       phone_number=phone_number,
                                                                       rsgb_attending=rsgb_attending,
                                                                       approved=approved)
            if new_station_id:
                # Create OK
                self.set_status(200)
                self.write(json.dumps({"message": "Station created. Returning you to the stations list...",
                                       "redirect_url": "/admin/stations"}))
                return
            else:
                self.set_status(500)
                self.write(
                    json.dumps({"message": "Failed to create the station. Please check the logs for more details."}))
                return

        else:
            self.set_status(400)
            self.write(json.dumps({"message": "Invalid action '" + action + "'"}))
            return

    def get_events_js(self):
        """Get data for events, mutated to be suitable for the admin temporary station page. This includes:
         * Removing any parameters of those events that the page doesn't need to know about
         * Replacing non-JSON-serializable objects with serializable equivalents.
         This allows us to dump Python objects (the output of this function) straight into JS rather than templating in the
         HTML template as an intermediary step."""

        output = []
        for e in self.application.db.get_all_events():
            output.append({
                "id": e.id,
                "start_time": e.start_time.isoformat(),
                "end_time": e.end_time.isoformat(),
                "notes_template": e.notes_template,
                "band_ids": [b.id for b in e.bands],
                "mode_ids": [m.id for m in e.modes]
            })
        return output
