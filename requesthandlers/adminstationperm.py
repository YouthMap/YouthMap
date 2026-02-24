import json

import tornado

from core.utils import populate_derived_fields_perm_station
from core.validation import validate_callsign, validate_free_text, validate_url, validate_phone, validate_email_address, \
    validate_latitude, validate_longitude
from mail.mailer import notify_owner_station_approved, notify_owner_station_approval_revoked, \
    notify_owner_station_deleted
from requesthandlers.base import BaseHandler


class AdminStationPermHandler(BaseHandler):
    """Handler for admin permanent station editing page"""

    @tornado.web.authenticated
    def get(self, slug):
        """The slug here is the permanent station ID, so e.g. the URL can be /admin/station/temp/1 to edit permanent
        station 1. A special slug of 'new' is also allowed, which sets up the form to create a permanent station rather
        than to edit one."""

        station_id = int(slug) if slug != "new" else None
        creating_new = (slug == "new")

        # Get data we need to include in the template
        station = self.application.db.get_permanent_station(station_id) if not creating_new else None
        if station:
            populate_derived_fields_perm_station(station)
        all_perm_station_types = self.application.db.get_all_permanent_station_types()

        # Render the template
        if station or creating_new:
            self.render("adminstationperm.html", station=station, creating_new=creating_new,
                        all_perm_station_types=all_perm_station_types)
        else:
            self.write("Station not found.")

    @tornado.web.authenticated
    def post(self, slug):
        """Handles POST requests for permanent station editing page. This supports three 'actions' depending on whether
        the Update or Delete button was clicked for an existing station, or the Create button was clicked for a new
        station, and provides the updated data to insert back into the database. The slug here is the permanent station
        ID, so e.g. the URL can be /admin/station/perm/1 to edit permanent station 1. A special slug of 'new' is also
        allowed, which sets up the form to create a permanent station rather than to edit one."""

        self.set_header("Content-Type", "application/json")

        station_id = int(slug) if slug != "new" else None

        # Get the action we have been asked to do
        action = self.get_argument("action")

        # Check for Delete action
        if action == "Delete":
            # Process the delete action
            station = self.application.db.get_permanent_station(station_id)
            ok = self.application.db.delete_permanent_station(station_id)
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
            edit_password, err_pw = validate_free_text(self.get_argument("edit_password"), "edit password",
                                                       max_length=200)

            err = next((x for x in
                        [err_callsign, err_club, err_notes, err_when, err_where, err_website, err_qrz, err_social,
                         err_email, err_phone, err_pw, err_lat, err_lon] if x is not None), None)
            if err:
                self.set_status(400)
                self.write(json.dumps({"message": err}))
                return

            # Get request arguments that don't need separate validation
            type_id = 0
            if self.get_argument("type", None):
                type_id = int(self.get_argument("type"))
            approved = True if self.get_argument("approved", None) else False

            # Check for approval changes to email the owner
            station = self.application.db.get_permanent_station(station_id)
            approval_happened = approved and not station.approved
            approval_revoked = station.approved and not approved

            # Process the update
            ok = self.application.db.update_permanent_station(station_id, callsign=callsign, club_name=club_name,
                                                              type_id=type_id,
                                                              latitude_degrees=latitude_degrees,
                                                              longitude_degrees=longitude_degrees,
                                                              meeting_when=meeting_when, meeting_where=meeting_where,
                                                              notes=notes, website_url=website_url, qrz_url=qrz_url,
                                                              social_media_url=social_media_url, email=email,
                                                              phone_number=phone_number, approved=approved,
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
            meeting_when, err_when = validate_free_text(self.get_argument("meeting_when", "") or "", "Meeting times",
                                                        max_length=200)
            meeting_where, err_where = validate_free_text(self.get_argument("meeting_where", "") or "", "Meeting place",
                                                          max_length=200)
            website_url, err_website = validate_url(self.get_argument("website_url", "") or "", "Website")
            qrz_url, err_qrz = validate_url(self.get_argument("qrz_url", "") or "", "QRZ page")
            social_media_url, err_social = validate_url(self.get_argument("social_media_url", "") or "",
                                                        "Social media")
            email, err_email = validate_email_address(self.get_argument("email", "") or "")
            phone_number, err_phone = validate_phone(self.get_argument("phone_number", "") or "")

            err = next((x for x in
                        [err_callsign, err_club, err_notes, err_when, err_where, err_website, err_qrz, err_social,
                         err_email, err_phone, err_lat, err_lon] if x is not None), None)
            if err:
                self.set_status(400)
                self.write(json.dumps({"message": err}))
                return

            # Get request arguments that don't need separate validation
            type_id = 0
            if self.get_argument("type", None):
                type_id = int(self.get_argument("type"))
            approved = True if self.get_argument("approved", None) else False

            # Process the create action
            new_station_id = self.application.db.add_permanent_station(callsign=callsign, club_name=club_name,
                                                                       type_id=type_id,
                                                                       latitude_degrees=latitude_degrees,
                                                                       longitude_degrees=longitude_degrees,
                                                                       meeting_when=meeting_when,
                                                                       meeting_where=meeting_where,
                                                                       notes=notes, website_url=website_url,
                                                                       qrz_url=qrz_url,
                                                                       social_media_url=social_media_url, email=email,
                                                                       phone_number=phone_number, approved=approved)

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
