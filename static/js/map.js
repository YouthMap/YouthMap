import { FeatureGroup, Map, Marker, TileLayer } from "leaflet";
import { Icon, PinSquarePanel } from "leaflet-extra-markers";


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
    });
    temp_stations.forEach(s => {
        // Skip temporary stations that have finished
        // TODO if a slug is provided we should show finished stations
        const end_time = luxon.DateTime.fromISO(s.end_time);
        alert(s.callsign + " " + s.end_time + " " + (luxon.DateTime.now() <= end_time));
        if (luxon.DateTime.now() <= end_time) {
            // Create a marker for the temporary station
            const marker = new Marker([s.latitude_degrees, s.longitude_degrees], {
                icon: new Icon({
                  accentColor: s.color,
                  svgFillImageSrc: "/upload/" + s.icon,
                  scale: 1.5,
                  svg: PinSquarePanel,
                }),
            }).addTo(markersLayer);
        }
    });
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