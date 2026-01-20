# YouthMap

Map for YOTA, JOTA and other Amateur Radio events involving young people.

This project is a work in progress and is still at a very early stage. Please stand by for updates coming soon!

### To Do List

* Database
    * Complete relational DB design
    * Implement the rest of the tables
    * Implement all access methods
        * Admins
            * Delete admin
            * Change own password
        * Events
            * ...
    * DB creation - move to some other method than init in Python code?
        * Remove DB file from repo?
    * Clean up old sessions from table on login?
* Admin panel
    * Use template
    * Implement all admin features
        * HTML
        * POST calls
* Login page
    * Use template - how best to do this with POST too?
* Map page
    * Use template
    * Implement UI
    * Implement all features
* Create/edit station - overlay on map or separate page?
* Config file e.g. host port
