import { FeatureGroup, Map, Marker, TileLayer } from "leaflet";
import { Icon, PinSquarePanel } from "leaflet-extra-markers";
import { DateTime } from "luxon";

var placingMarker;
var addStationMarker;


// Set up the map
function setUpMap() {
    // Create map
    const map = new Map("map", {
        zoomControl: true,
        minZoom: 2,
        maxZoom: 16
    });

    // Add basemap
    const backgroundTileLayer = new TileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    // Display a default view.
    map.setView([30, 0], 3);

    // Set the onclick action to handle the user clicking on the map background. Won't do anything unless placingMarker
    // has been set true.
    map.on('click',	function(e) {
        if (placingMarker) {
            addStationMarker = new Marker(e.latlng, {
                icon: new Icon({
                  color: "#0d6efd",
                  accentColor: "#0d6efd",
                  content: "🌟",
                  scale: 1.5,
                  svg: PinSquarePanel,
                }),
                draggable:'true'
            }).addTo(map);
            addStationMarker.on('dragend', function(event){
                var addStationMarker = event.target;
                var position = addStationMarker.getLatLng();
                setTimeout(function() { new bootstrap.Modal('#addStationModal2').show(); }, 500);
            });

            placingMarker = false;
            setTimeout(function() { new bootstrap.Modal('#addStationModal2').show(); }, 500);
        }
    });

    return map;
}

// Based on the filter options the user has selected under "Map settings", should this permanent station have a marker
// displayed on the map? Returns true if the filter selection is "all stations", or if it's "permanent stations" and
// the permanent station type is set to "all", or if the permanent station type is set to an ID that matches the type ID
// of the station we are checking.
function perm_station_matches_filters(s) {
    const station_type = $("input:radio[name=station_type]:checked").val();
    if (station_type == "all") {
        return true;
    } else if (station_type == "temp") {
        return false;
    } else {
        const type = $("#type").val();
        if (type == "all") {
            return true;
        } else {
            return type == s.type.id;
        }
    }
}

// Based on the filter options the user has selected under "Map settings", should this temporary station have a marker
// displayed on the map? First we check whether we are displaying temporary stations at all, and if so whether we are
// filtering to just those associated with a certain event (or the "other" event). Then, we also need to check
// whether there is an additional filter that removes event stations which have expired, and whether the band/mode
// filters allow this station. To streamline what would otherwise be a large method, we just check for mismatches and
// return false when found; if it makes it all the way through the method, it's survived all the filters so return true.
function temp_station_matches_filters(s) {
    // Check type
    const station_type = $("input:radio[name=station_type]:checked").val();
    if (station_type == "perm") {
        return false;
    } else if (station_type == "temp") {
        // Check event ID
        const event = $("#event").val();
        if (event != "all" && event != "other" && (s.event == null || event != s.event.id)) {
            return false;
        } else if (event == "other" && s.event != null) {
            return false;
        }

        // Check bands
        const band = $("#band").val();
        if (band != "any" && !s.bands.some(b => b.id == band)) {
            return false;
        }

        // Check modes
        const mode = $("#mode").val();
        if (mode != "any" && !s.modes.some(m => m.id == mode)) {
            return false;
        }
    }

    // Check expiry
    const end_time = DateTime.fromISO(s.end_time);
    if (!($("#allow_past").is(':checked')) && DateTime.now() > end_time) {
        return false;
    }

    return true;
}

// Create markers based on the user's current filters. Any markers that do not match the current filter will be removed.
function createMarkers(markersLayer) {
    // Clear existing markers
    markersLayer.clearLayers();

    // Create new ones for all permanent and temporary stations that match the filters.
    perm_stations.forEach(s => {
        if (perm_station_matches_filters(s)) {
            // Create a marker for the permanent station
            const marker = new Marker([s.latitude_degrees, s.longitude_degrees], {
                icon: new Icon({
                  accentColor: s.color,
                  svgFillImageSrc: "/upload/" + s.icon,
                  scale: 1.5,
                  svg: PinSquarePanel,
                }),
            }).addTo(markersLayer);
            marker.bindPopup(getPopupTextForPerm(s));
        }
    });
    temp_stations.forEach(s => {
        if (temp_station_matches_filters(s)) {
            // Create a marker for the temporary station
            const marker = new Marker([s.latitude_degrees, s.longitude_degrees], {
                icon: new Icon({
                  accentColor: s.color,
                  svgFillImageSrc: "/upload/" + s.icon,
                  scale: 1.5,
                  svg: PinSquarePanel,
                }),
            }).addTo(markersLayer);
            marker.bindPopup(getPopupTextForTemp(s));
        }
    });
}

// Get popup text for a permanent station
function getPopupTextForPerm(s) {
    var text = "<p><b>" + s.callsign + "</b><br/>" + s.club_name + "</p>";
    text = text + "<p style='text-align: right;'><a class='nav-link ml-auto' href='/view/station/perm/" + s.id + "'>More details &raquo;</a></p>";
    return text;
}

// Get popup text for a temporary station
function getPopupTextForTemp(s) {
    var text = "<p><b>" + s.callsign + "</b><br/>" + s.club_name + "<br/>";
    if (s.event) {
        text = text + "at " + s.event.name;
    }
    text = text + "</p>";
    if (s.rsgb_attending) {
        text = text + "<p><img src='/img/rsgb-logo.png' alt='RSGB logo' class='me-2' style='height: 2em;'/>RSGB attending</p>";
    }
    text = text + "<p>" + s.humanized_start_end + "</p>";
    text = text + "<p style='text-align: right;'><a class='nav-link ml-auto' href='/view/station/temp/" + s.id + "'>More details &raquo;</a></p>";
    return text;
}

// Hides past events in the event select (or not), depending on whether "show past events" is enabled.
function refreshEventSelect() {
    $("#event option").each(function() {
        if ($("#allow_past").is(':checked')) {
            // Allow past events is true, so enable all events in the list
            $(this).prop("disabled", false);
            $(this).prop("hidden", false);

        } else {
            events.forEach(e => {
                // Find the full data for the event
                if (e.id == this.value) {
                    const end_time = DateTime.fromISO(e.end_time);
                    if (DateTime.now() > end_time) {
                        // Event has already finished, so disable & hide this entry from the list
                        $(this).prop("disabled", true);
                        $(this).prop("hidden", true);

                        // If the user has selected this option and it's now disabled, switch to the default "all" option.
                        if ($(this).prop("selected")) {
                            $("#event").val("all");
                        }
                    } else {
                        // Event is running now or in the future, so allow this entry in the list
                        $(this).prop("disabled", false);
                        $(this).prop("hidden", false);
                    }
                }
            });
        }
    });
}

// Shows and hides areas of the Map Settings panel depending on what's just been selected
function showHideSettingsAreas() {
    var selectedValue = $("input[name='station_type']:checked").val();
        if (selectedValue == "perm") {
            $("#permDetails").show();
            $("#tempDetails").hide();
        } else if (selectedValue == "temp") {
            $("#permDetails").hide();
            $("#tempDetails").show();
        } else {
            $("#permDetails").hide();
            $("#tempDetails").hide();
        }
}

// Callback on any filter control being clicked. Regenerates the markers to match the new filter settings, and sets up
// the event select to show/hide past events depending on the filter setting. We run refreshEventSelect() first because
// in one specific case (if we have a past event selected and have just toggled off allowing past events) this method
// actually changes the controls (sets the event back to "All") so we need to redo the markers *after* finding this out.
function filtersUpdated(markersLayer) {
    refreshEventSelect();
    createMarkers(markersLayer);
}

// Startup
$(document).ready(function() {
    // Set up map
    const map = setUpMap();

    // Add marker layer
    const markersLayer = new FeatureGroup();
    markersLayer.addTo(map);

    // Ensure whatever the HTML selections are by default in the Map Settings panel are applied on startup. This will
    // also cause the first-time marker generation to happen.
    showHideSettingsAreas();
    filtersUpdated(markersLayer);

    // Zoom to fit the markers
    map.fitBounds(markersLayer.getBounds().pad(0.5));

    // Add click handler to the button that lets you add a station to the map
    $("button#addStationGetStarted").click(function(){ placingMarker = true; });
    // Add click handler to the cancel button on the second "add station" modal, as this is to cancel the whole process
    // so we need to remove the marker we created
    $("button#addStationCancel").click(function(){ map.removeLayer(addStationMarker); });
    // Add click handler to the OK button on the second "add station" modal, which will take us to the next stage
    $("button#addStationSetUp").click(function(){ window.location.href = "/create/station/type?lat=" + addStationMarker.getLatLng().lat + "&lon=" + addStationMarker.getLatLng().lng });

    // Add listeners to filter controls
    $("input.stationTypeRadio").click(function(){ showHideSettingsAreas(); filtersUpdated(markersLayer); });
    $("select#type").click(function(){ filtersUpdated(markersLayer); });
    $("select#event").click(function(){ filtersUpdated(markersLayer); });
    $("select#band").click(function(){ filtersUpdated(markersLayer); });
    $("select#mode").click(function(){ filtersUpdated(markersLayer); });
    $("input#allow_past").click(function(){ filtersUpdated(markersLayer); });
});