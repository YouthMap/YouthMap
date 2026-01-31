import { LayerGroup, Map, Marker, TileLayer } from "leaflet";
import { Icon, PinCirclePanel } from "leaflet-extra-markers";

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

    // Add marker layer
    const markersLayer = new LayerGroup();
    markersLayer.addTo(map);

    // Display a default view.
    map.setView([30, 0], 3);

    const marker = new Marker(map.getCenter(), {
        icon: new Icon({
          accentColor: "firebrick",
          color: "indianred",
          content: "TEST",
          contentColor: "white",
          scale: 1,
          svg: PinCirclePanel,
        }),
    }).addTo(markersLayer);
}

// Startup
$(document).ready(function() {
    // Set up map
    setUpMap();
    // todo delete
    alert(perm_stations);
});