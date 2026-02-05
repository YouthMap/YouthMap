from core.utils import temp_station_to_json_for_user_frontend, perm_station_to_json_for_user_frontend, \
    humanize_start_end
from requesthandlers.base import BaseHandler


class ViewStationHandler(BaseHandler):
    """Handler for station view page"""

    def get(self, perm_or_temp_slug, station_id_slug):
        """Two slugs are provided here. The first is "perm" or "temp", and the second is the station ID within that
        category, so e.g. the URL can be /view/station/temp/1 to view permanent station 1."""

        station_id = int(station_id_slug)

        # Get data we need to include in the template
        station = None
        station_json = None
        if perm_or_temp_slug == "perm":
            station = self.application.db.get_permanent_station(station_id)
            station_json = perm_station_to_json_for_user_frontend(station)
        elif perm_or_temp_slug == "temp":
            station = self.application.db.get_temporary_station(station_id)
            station.humanized_start_end = humanize_start_end(station.start_time, station.end_time)
            station_json = temp_station_to_json_for_user_frontend(station)

        # Render the template. Supply the real object for the template and the JSON version to load more easily into
        # the map.
        self.render("viewstation.html", type=perm_or_temp_slug, station=station, station_json=station_json)

    def post(self, perm_or_temp_slug, station_id_slug):
        """Handle the user entering an edit password and clicking Edit or Delete. This supports two 'actions' depending
         on whether the Edit or Delete button was clicked,and provides the user's edit password to compare against the
         station. Two slugs are provided here. The first is "perm" or "temp", and the second is the station ID within that
        category, so e.g. the URL can be /view/station/temp/1 to view permanent station 1."""

        station_id = int(station_id_slug)
        user_edit_password = self.get_argument("edit_password")
        edit_password_good = False

        # Check the edit password
        if perm_or_temp_slug == "perm":
            station = self.application.db.get_permanent_station(station_id)
            edit_password_good = station.edit_password == user_edit_password
        elif perm_or_temp_slug == "temp":
            station = self.application.db.get_temporary_station(station_id)
            edit_password_good = station.edit_password == user_edit_password

        if not edit_password_good:
            self.write("Password incorrect")
            return

        # Get the action we have been asked to do
        action = self.get_argument("action")

        # Check for Edit action
        if action == "Edit":
            self.redirect(
                "/edit/station/" + perm_or_temp_slug + "/" + station_id_slug + "?edit_password=" + user_edit_password)

        # Check for Delete action
        elif action == "Delete":
            if perm_or_temp_slug == "perm":
                self.application.db.delete_permanent_station(station_id)
            elif perm_or_temp_slug == "temp":
                self.application.db.delete_temporary_station(station_id)
            self.redirect("/")

    # TODO
