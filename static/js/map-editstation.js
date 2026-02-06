import { FeatureGroup, Map, Marker, TileLayer } from "leaflet";


// Set up the map
function setUpMap() {
    // Create map
    const map = new Map("map", {
        zoomControl: false,
        minZoom: 2,
        maxZoom: 16
    });

    // Add basemap
    const backgroundTileLayer = new TileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    return map;
}

// Create marker and add support for updating the form's hidden lat/lon fields when finished dragging.
function createMarker(map) {
    const marker = new Marker([latitude_degrees, longitude_degrees], {draggable:'true'}).addTo(map);
    marker.on('dragend', function(event){
        var marker = event.target;
        var position = marker.getLatLng();
        $("#latitude_degrees").val(position.lat);
        $("#longitude_degrees").val(position.lng);
    });
}

// Startup
$(document).ready(function() {
    // Set up map
    const map = setUpMap();

    // Create marker
    createMarker(map);

    // Zoom to it
    map.setView([latitude_degrees, longitude_degrees], 12);
});