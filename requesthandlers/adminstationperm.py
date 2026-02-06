import tornado

from core.utils import populate_derived_fields_perm_station
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
        self.render("adminstationperm.html", station=station, creating_new=creating_new,
                    all_perm_station_types=all_perm_station_types)

    @tornado.web.authenticated
    def post(self, slug):
        """Handles POST requests for permanent station editing page. This supports three 'actions' depending on whether
        the Update or Delete button was clicked for an existing station, or the Create button was clicked for a new
        station, and provides the updated data to insert back into the database. The slug here is the permanent station
        ID, so e.g. the URL can be /admin/station/perm/1 to edit permanent station 1. A special slug of 'new' is also
        allowed, which sets up the form to create a permanent station rather than to edit one."""

        station_id = int(slug) if slug != "new" else None

        # Get the action we have been asked to do
        action = self.get_argument("action")

        # Check for Delete action
        if action == "Delete":
            # Process the delete action
            ok = self.application.db.delete_permanent_station(station_id)
            if ok:
                # Delete OK, go back to stations list
                self.redirect("/admin/stations")
            else:
                self.write("Failed to delete station")

        # Check for Update action
        elif action == "Update":
            # Get request arguments
            callsign = self.get_argument("callsign")
            club_name = self.get_argument("club_name")
            type_id = 0
            if self.get_argument("type", None):
                type_id = int(self.get_argument("type"))
            latitude_degrees = float(self.get_argument("latitude_degrees"))
            longitude_degrees = float(self.get_argument("longitude_degrees"))
            meeting_when = self.get_argument("meeting_when")
            meeting_where = self.get_argument("meeting_where")
            notes = self.get_argument("notes", None)
            notes = notes if notes else ""
            website_url = self.get_argument("website_url", None)
            website_url = website_url if website_url else ""
            qrz_url = self.get_argument("qrz_url", None)
            qrz_url = qrz_url if qrz_url else ""
            social_media_url = self.get_argument("social_media_url", None)
            social_media_url = social_media_url if social_media_url else ""
            email = self.get_argument("email", None)
            email = email if email else ""
            phone_number = self.get_argument("phone_number", None)
            phone_number = phone_number if phone_number else ""
            approved = True if self.get_argument("approved", None) else False
            edit_password = self.get_argument("edit_password")

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
                # Update OK, just reload the page which will have the new data in it
                self.redirect("/admin/station/perm/" + slug)
            else:
                self.write("Failed to update station")
                return

            # Check for Create action
        elif action == "Create":
            # Get request arguments
            callsign = self.get_argument("callsign")
            club_name = self.get_argument("club_name")
            type_id = 0
            if self.get_argument("type", None):
                type_id = int(self.get_argument("type"))
            latitude_degrees = float(self.get_argument("latitude_degrees"))
            longitude_degrees = float(self.get_argument("longitude_degrees"))
            meeting_when = self.get_argument("meeting_when")
            meeting_where = self.get_argument("meeting_where")
            notes = self.get_argument("notes", None)
            notes = notes if notes else ""
            website_url = self.get_argument("website_url", None)
            website_url = website_url if website_url else ""
            qrz_url = self.get_argument("qrz_url", None)
            qrz_url = qrz_url if qrz_url else ""
            social_media_url = self.get_argument("social_media_url", None)
            social_media_url = social_media_url if social_media_url else ""
            email = self.get_argument("email", None)
            email = email if email else ""
            phone_number = self.get_argument("phone_number", None)
            phone_number = phone_number if phone_number else ""
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
                # Create OK, just reload the page which will have the new data in it
                self.redirect("/admin/station/perm/" + str(new_station_id))
            else:
                self.write("Failed to update station")
                return

            self.write("not implemented yet")

        else:
            self.write("Invalid action '" + action + "'")
