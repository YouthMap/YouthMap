# Developer Documentation

Youth Map is a single integrated program that includes a web server, database and access code, static HTML/CSS assets, and JavaScript code to provide the web site.

## Code Structure

### Web Server

The web server code uses Python's Tornado library. This serves both static assets (JS, CSS) and HTML files that are generated from templates. The same request handler classes that provide the HTML on GET requests also provide the processing of data and responses to POST requests.

The code is structured as follows:

* `/youthmap.py`: Main entry point, extends `tornado.web.Application`
* `/requesthandlers/*.py`: Contains the custom Tornado `RequestHandlers`. There is one for each HTML page which provides `get()` and `post()` methods as necessary. There is also a `base.py` containing the `BaseHandler` class which all other `RequestHandler`s extend, which deals with authentication and session handling.
* `/templates/*.html`: Contains the templates used by the `RequestHandlers` to generate HTML in response to GET requests. As per the point above, there is generally one per site page. There is also a `base.html` which provides the `<head>`-type HTML content, which is extended by the other templates. There are also `base-std.html` and `base-map.html`. These provide an extre set of content inside the HTML body which wraps the page content. This is different for the main map page (which uses `base-map.html`) and all other pages (which use `base-std.html`) because the map page has the "Add your station" button in the header and other layout oddities relating to displaying the map. In essence the inheritance tree is:
  * Main map page -> `base-map.html` -> `base.html`
  * Any other page -> `base-std.html` -> `base.html`.
* `/static/css/*`: Statically served CSS files.
* `/static/js/*`: Statically served JavaScript files. These are implemented as ES6 modules.
* `/static/img/*`: Statically served image files, such as the site logo.

### Database

Currently, Youth Map uses a SQLite file-based database, which is created on startup if it's missing (or it's the first time running the software). The interface is implemented using SQLalchemy to provide data access, which means that the backing database can be swapped to e.g. MySQL when the site nears production readiness, if necessary.

The code is structured as follows:

* `/database/__init__.py`: Creates the database and populates it with default content if required.
* `/database/models.py`: Defines the key data tables.
* `/database/base.py`: Defines the relational lookup tables.
* `/database/operations.py`: Provides the data access methods that the rest of the application uses. For example there are `add`, `update` and `delete` methods for users, events, stations, etc.
* `/database/utils.py`: Provides utilities used by methods in `operations.py`, for example for creating and hashing passwords.

The data is structured as follows:

* `/data/database.db`: The default location of the SQLite database.

### Other Files

The other areas in the codebase are as follows:

* `/core/*.py`: Python functionality not relating directly to the web server or database, for example config file handling and general utilities. 
* `/data/upload/*`: A location for user-uploaded files. Currently this is limited to PNG icons to use for the markers. Some defaults are provided in the repository but on a live running site administrators will be able to manage these and upload their own.
* `/docs/*`: Contains this documentation.

## Design Choices

### Interface between Python and JavaScript

In general, HTML pages served by Tornado are populated with data using templates in the standard way, such as "Username: `{{user.name}}`". However, sometimes (especially with the maps), it is necessary to get data into JavaScript objects rather than simply into HTML. In Tornado, only HTML templates can include tags like this, static JavaScript files cannot. Within the codebase there are two patterns for handling this:

For simple data, such as the position, colour and icon for a single station marker, this is done via a `script` block in the HTML template. For example, the last few lines of `viewstation.html` set up JavaScript variables using templating, before calling the separate JavaScript module that will take this data and load the map:

```html
<script>
    let latitude_degrees = {{ float(station.latitude_degrees) }};
    let longitude_degrees = {{ float(station.longitude_degrees) }};
    let color = "{{ station.color }}";
    let icon = "{{ station.icon }}";
</script>
<script type="module" src="/js/map-viewstation.js"></script>
```

For the main map, we need a complex data structure of arrays of two different types of station, each of which has various parameters. Here, this approach would get very complex in the HTML template. Instead, a different approach is taken using the `get_permanent_stations_for_map_js()` and `get_temporary_stations_for_map_js()` methods in `MapHandler` (`map.py`) to transform the database objects into JSON-serialisable objects. The resulting JSON is then dumped wholesale into JavaScript objects in `map.html`:

```html
<script>
    let perm_stations = JSON.parse({% raw json_encode(perm_stations_json) %});
    let temp_stations = JSON.parse({% raw json_encode(temp_stations_json) %});
</script>
<script type="module" src="/js/map.js"></script>
```