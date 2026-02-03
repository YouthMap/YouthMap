import { FeatureGroup, Map, Marker, TileLayer } from "leaflet";
import { Icon, PinSquarePanel } from "leaflet-extra-markers";
import { DateTime, Interval } from "luxon";


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

    return map;
}

// Create marker
function createMarker(map) {
    const marker = new Marker([station.latitude_degrees, station.longitude_degrees], {
        icon: new Icon({
          accentColor: station.color,
          svgFillImageSrc: "/upload/" + station.icon,
          scale: 1.5,
          svg: PinSquarePanel,
        }),
    }).addTo(map);
}

// Startup
$(document).ready(function() {
    // Set up map
    const map = setUpMap();

    // Create marker
    createMarker(map);

    // Zoom to it
    map.setView([station.latitude_degrees, station.longitude_degrees], 12);
});