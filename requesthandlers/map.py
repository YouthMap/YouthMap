import json

from core.utils import populate_derived_fields_temp_station, populate_derived_fields_perm_station
from requesthandlers.base import BaseHandler


# noinspection PyUnresolvedReferences
class MapHandler(BaseHandler):
    """Handler for the main map page. This only supports a GET but comes in two flavours, one of which is for the base
    URL (/) and the other is when a slug is provided. If a slug is provided, the whole station and event dataset is sent
    to the frontend anyway, the only difference is that the HTML selects under "Map settings" are preconfigured to
    display either just a certain event, or just a certain permanent station type, depending on what the slug was."""

    def get(self, slug=None):
        # Work out whether we have a slug and which event or permanent station type it corresponds to
        all_perm_station_types = self.application.db.get_all_permanent_station_types()
        all_events = self.application.db.get_all_events()
        preselect_type = None
        preselect_event = None
        if slug:
            permanent_types_matching_slug = [t for t in all_perm_station_types if t.name.lower() == slug.lower()]
            events_matching_slug = [e for e in all_events if e.url_slug.lower() == slug.lower()]
            preselect_type = permanent_types_matching_slug[0] if len(permanent_types_matching_slug) > 0 else None
            preselect_event = events_matching_slug[0] if len(events_matching_slug) > 0 else None

            # If it didn't match anything, that's invalid so redirect back to home
            if not preselect_type and not preselect_event:
                self.redirect("/")

        # Get other data we need to include in the template. Convert to JSON here so we can load it straight up in JS.
        temp_stations_json = json.dumps(self.get_temporary_stations_js())
        perm_stations_json = json.dumps(self.get_permanent_stations_js())
        all_bands = self.application.db.get_all_bands()
        all_modes = self.application.db.get_all_modes()
        all_events_json = json.dumps(self.get_events_js())

        # Render the template
        self.render("map.html", temp_stations_json=temp_stations_json, perm_stations_json=perm_stations_json,
                    all_bands=all_bands, all_modes=all_modes, all_perm_station_types=all_perm_station_types,
                    all_events=all_events, all_events_json=all_events_json, preselect_event=preselect_event,
                    preselect_type=preselect_type)

    def get_permanent_stations_js(self):
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

    def get_temporary_stations_js(self):
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

    def get_events_js(self):
        """Get data for events, mutated to be suitable for the main map. This includes:
         * Removing any parameters of those events that the map doesn't need to know about
         * Sorting by event start time, reversed (so the furthest future events are at the start, and furthest past
         events are at the bottom).
         * Replacing non-JSON-serializable objects with serializable equivalents.
         This allows us to dump Python objects (the output of this function) straight into JS rather than templating in
         the HTML template as an intermediary step."""

        output = []
        events = sorted(self.application.db.get_all_events(), key=lambda x: x.start_time, reverse=True)
        for e in events:
            output.append({
                "id": e.id,
                "start_time": e.start_time.isoformat(),
                "end_time": e.end_time.isoformat()
            })
        return output
