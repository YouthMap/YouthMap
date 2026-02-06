import json

from core.utils import populate_derived_fields_temp_station, populate_derived_fields_perm_station
from requesthandlers.base import BaseHandler


class MapHandler(BaseHandler):
    """Handler for the main map page"""

    def get(self):
        # Get data we need to include in the template. Convert to JSON here so we can load it straight up in JS.
        temp_stations_json = json.dumps(self.get_temporary_stations_for_map_js())
        perm_stations_json = json.dumps(self.get_permanent_stations_for_map_js())

        # Render the template
        self.render("map.html", temp_stations_json=temp_stations_json, perm_stations_json=perm_stations_json)



    def get_permanent_stations_for_map_js(self):
        """Get data for permanent stations, mutated to be suitable for the main map. This includes:
         * Removing any stations that are not approved yet
         * Removing any parameters of those stations that the map doesn't need to know about - in particular removing
           edit_password
         * Replacing non-JSON-serializable objects with serializable equivalents.
         This allows us to dump Python objects (the output of this function) straight into JS rather than templating in the
         HTML template as an intermediary step."""

        output = []
        for s in self.application.db.get_all_permanent_stations():
            if s.approved:
                populate_derived_fields_perm_station(s)
                output.append({
                    "id": s.id,
                    "callsign": s.callsign,
                    "club_name": s.club_name,
                    "latitude_degrees": float(s.latitude_degrees),
                    "longitude_degrees": float(s.longitude_degrees),
                    "icon": s.icon,
                    "color": s.color,
                    "type": {"id": s.type.id, "name": s.type.name}
                })
        return output


    def get_temporary_stations_for_map_js(self):
        """Get data for temporary stations, mutated to be suitable for the main map. This includes:
         * Removing any stations that are not approved yet
         * Removing any parameters of those stations that the map doesn't need to know about - in particular removing
           edit_password
         * Replacing non-JSON-serializable objects with serializable equivalents.
         This allows us to dump Python objects (the output of this function) straight into JS rather than templating in the
         HTML template as an intermediary step."""

        output = []
        for s in self.application.db.get_all_temporary_stations():
            if s.approved:
                populate_derived_fields_temp_station(s)
                output.append({
                    "id": s.id,
                    "callsign": s.callsign,
                    "club_name": s.club_name,
                    "start_time": s.start_time.isoformat(),
                    "end_time": s.end_time.isoformat(),
                    "humanized_start_end": s.humanized_start_end,
                    "latitude_degrees": float(s.latitude_degrees),
                    "longitude_degrees": float(s.longitude_degrees),
                    "icon": s.icon,
                    "color": s.color,
                    "rsgb_attending": s.rsgb_attending,
                    "event": {"id": s.event.id, "name": s.event.name} if s.event else None,
                    "bands": [{"id": b.id, "name": b.name} for b in s.bands],
                    "modes": [{"id": m.id, "name": m.name} for m in s.modes]
                })
        return output