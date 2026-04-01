# Sysadmin Documentation

Youth Map is designed to run in a single place on the web, to facilitate coordination between Amateur Radio youth
groups. You should not need to run your own copy. However, if you do (and for reference for the team running the "
official" copy), instructions on how to set up Youth Map on a web server are included here.

### Download, install and run

To download and set up Youth Map on a Debian server, run the following commands. Other operating systems will likely be
similar.

Replace the string `##tagname##` with the tagged version of Youth Map that you want to run. Skip this line entirely to
use the latest development code from the `main` branch.

```bash
git clone git@github.com:YouthMap/YouthMap.git youthmap
cd youthmap
git checkout ##tagname##
python3 -m venv ./.venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
```

As for *where* in your filesystem to run Youth Map from, and thus where to run those commands, that's up to you. The
following instructions assume you have created a new user called `youthmap` to run the site as, and installed it from
`/home/youthmap`. You should not run Youth Map as `root` or a user with `sudo` privileges, as this increases the risk of
exploit.

The `data/` directory within the Youth Map application directory must be writable by the user that runs the Python
process, as the application stores its database and uploaded files there. If you are running Youth Map as a dedicated
user (e.g. `youthmap` as described above), ensure that user owns this directory:

```bash
sudo chown youthmap data/
```

The rest of the structure needs to be readable by the user that Youth Map runs as, but not necessarily writeable.

To run the software this time and any future times you want to run it directly from the command line, use the following
commands. Replace `##your-secret-here##` with a long random string (e.g. the output of `openssl rand -hex 32`). Keeping
the same string will mean that existing user cookies remain valid; changing it will effectively log all users out.

```bash
source .venv/bin/activate
COOKIE_SECRET=##your-secret-here## python3 youthmap.py
python3 youthmap.py
```

You will see a log entry that includes the TCP port on which the server is running. You can then navigate to the
corresponding address in a browser window, e.g. `http://localhost:8080`.

The default port may need to be changed, in case you have other software on the server already bound to port 8080. The
port, and other settings, can be configured in `config.yml` if necessary.

As an alternative to this setup, you can host Youth Map in a Docker
container. [Click here for instructions.](./sysadmin.md)

### systemd configuration

If you want Youth Map to run automatically on startup on a Linux distribution that uses `systemd`, follow the
instructions here. For distros that don't use `systemd`, or Windows/OSX/etc., you can find generic instructions for your
OS online.

Create a file at `/etc/systemd/system/youthmap.service`. Give it the following content, adjusting for the user you want
to run it as and the directory in which you have installed it, as well as setting `##your-secret-here##` as described
above.

```
[Unit]
Description=YouthMap
After=syslog.target network.target

[Service]
Type=simple
User=youthmap
WorkingDirectory=/home/youthmap/youthmap
ExecStart=/home/youthmap/youthmap/.venv/bin/python /home/youthmap/youthmap/youthmap.py --serve-in-foreground
Environment=COOKIE_SECRET=##your-secret-here##
Restart=on-abort

[Install]
WantedBy=multi-user.target
```

Run the following:

```bash
sudo systemctl daemon-reload
sudo systemctl enable youthmap
sudo systemctl start youthmap
```

Check the service has started up correctly with `sudo journalctl -u youthmap -f`.

### nginx Reverse Proxy configuration

Web servers generally serve their pages from port 80. However, it's best not to serve Youth Map's web interface directly
on port 80, as that requires root privileges on a Linux system. It also and prevents us using HTTPS to serve a secure
site, since Youth Map itself doesn't directly support acting as an HTTPS server. The normal solution to this is to use
a "reverse proxy" setup, where a general web server handles HTTP and HTTP requests (to port 80 & 443 respectively), then
passes on the request to the back-end application (in this case Youth Map). nginx is a common choice for this general
web server.

To set up nginx as a reverse proxy that sits in front of Youth Map, first ensure it's installed e.g.
`sudo apt install nginx`, and enabled e.g. `sudo systemd enable nginx`.

Create a file in `/etc/nginx/sites-available/` called `youthmap`. Give it the following contents, replacing
`youthmap.com` with the domain name on which you want to run Youth Map. If you changed the port on which Youth Map runs,
update that on the "proxy_pass" line too.

```nginx
server {
    server_name youthmap.com;

    # Wellknown area for Lets Encrypt
    location /.well-known/ {
        alias /var/www/html/.well-known/;
    }
    
    location / {
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_pass http://127.0.0.1:8080;
    }
}
```

Now, make a symbolic link to enable the site:

```bash
cd /etc/nginx/sites-enabled
sudo ln -sf ../sites-available/youthmap
```

Test that your nginx config isn't broken using `nginx -t`. If it works, restart nginx with
`sudo systemctl restart nginx`.

If you haven't already done so, set up a DNS entry to make sure requests for your domain name end up at the server
that's running Youth Map.

You should now be able to access the web interface by going to the domain from your browser, using HTTP.

Once that's working, [install certbot](https://certbot.eff.org/instructions?ws=nginx&os=snap) onto your server. Run it
as root, and when prompted pick your domain name from the list. After a few seconds, it should successfully provision a
certificate and modify your nginx config files automatically. You should then be able to access the site via HTTPS.

### Serving static files directly from nginx

The configuration above proxies every request through to the Youth Map application, including requests for static
files (CSS, JavaScript, images, etc.) under the `/static/` path. Since these files never change at runtime, it is more
efficient to have nginx serve them directly from disk, bypassing the application entirely. To do this, add a
`location /static/` block before the catch-all `location /` block, pointing nginx at the `static` directory inside your
Youth Map installation:

Note that nginx's worker process (typically `www-data`) must be able to traverse every directory in the path to the
static files. Home directories on Linux default to `700` (owner-only access), so if Youth Map is installed under
`/home/youthmap/`, nginx will give a 403 error for the static files. You can work around this by granting world-execute
permission on the home directory:

```bash
sudo chmod o+x /home/youthmap
```

Consider the implications of this in terms of any other users on the machine and what they have access to.

```nginx
server {
    server_name youthmap.com;

    # Wellknown area for Lets Encrypt
    location /.well-known/ {
        alias /var/www/html/.well-known/;
    }

    # Serve static assets directly without going through the application
    location /static/ {
        alias /home/youthmap/youthmap/static/;
    }

    location / {
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_pass http://127.0.0.1:8080;
    }
}
```

Adjust the path on the `alias` line to match the directory in which you have installed Youth Map. After editing the
file, test and reload nginx as before (`nginx -t` then `sudo systemctl reload nginx`).
