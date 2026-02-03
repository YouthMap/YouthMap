import { FeatureGroup, Map, Marker, TileLayer } from "leaflet";
import { Icon, PinSquarePanel } from "leaflet-extra-markers";
import { DateTime } from "luxon";


// Set up the map
function setUpMap() {
    // Create map
    const map = new Map("map", {
        zoomControl: true,
        minZoom: 2,
        maxZoom: 12
    });

    // Add basemap
    const backgroundTileLayer = new TileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    // Display a default view.
    map.setView([30, 0], 3);

    return map;
}

// Create markers based on the user's current filters. Any markers that do not match the current filter will be removed.
function createMarkers(markersLayer) {
    // Clear existing markers
    markersLayer.clearLayers();

    // Create new ones for all permanent and temporary stations that match the filters.
    // TODO filtering
    perm_stations.forEach(s => {
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
    });
    temp_stations.forEach(s => {
        // Skip temporary stations that have finished
        // TODO if a slug is provided we should show finished stations
        const end_time = DateTime.fromISO(s.end_time);
        if (DateTime.now() <= end_time) {
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
        text = text + "at " + s.event.name + "<br/>";
    }
    text = text + s.humanized_start_end + "</p><p style='text-align: right;'><a class='nav-link ml-auto' href='/view/station/temp/" + s.id + "'>More details &raquo;</a></p>";
    return text;
}

// Startup
$(document).ready(function() {
    // Set up map
    const map = setUpMap();

    // Add marker layer
    const markersLayer = new FeatureGroup();
    markersLayer.addTo(map);

    // Create markers
    createMarkers(markersLayer);

    // Zoom to fit
    map.fitBounds(markersLayer.getBounds().pad(0.5));
});