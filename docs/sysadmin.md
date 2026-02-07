# Sysadmin Documentation

Youth Map is designed to run in a single place on the web, to facilitate coordination between Amateur Radio youth groups. You should not need to run your own copy. However, if you do (and for reference for the team running the "official" copy), instructions on how to set up Youth Map on a web server are included here.

To download and set up Youth Map on a Debian server, run the following commands. Other operating systems will likely be similar.

*Note:* Replace the string `##tagname##` with the tagged version of Youth Map that you want to run. Skip this line entirely to use the latest development code from the `main` branch.

```bash
git clone git@github.com:YouthMap/YouthMap.git youthmap
cd youthmap
git checkout ##tagname##
python3 -m venv ./.venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
```

To run the software this time and any future times you want to run it directly from the command line:

```bash
source .venv/bin/activate
python3 youthmap.py
```

You will see a log entry that includes the TCP port on which the server is running. You can then navigate to the corresponding address in a browser window, e.g. `http://localhost:8080`.

The default port may need to be changed, in case you have other software on the server already bound to port 8080. The port, and other settings, can be configured in `config.yml` if necessary.

### systemd configuration

If you want Youth Map to run automatically on startup on a Linux distribution that uses `systemd`, follow the instructions here. For distros that don't use `systemd`, or Windows/OSX/etc., you can find generic instructions for your OS online.

Create a file at `/etc/systemd/system/youthmap.service`. Give it the following content, adjusting for the user you want to run it as and the directory in which you have installed it:

```
[Unit]
Description=YouthMap
After=syslog.target network.target

[Service]
Type=simple
User=youthmap
WorkingDirectory=/home/youthmap/youthmap
ExecStart=/home/youthmap/youthmap/.venv/bin/python /home/youthmap/youthmap/youthmap.py --serve-in-foreground
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

Web servers generally serve their pages from port 80. However, it's best not to serve Youth Map's web interface directly on port 80, as that requires root privileges on a Linux system. It also and prevents us using HTTPS to serve a secure site, since Spothole itself doesn't directly support acting as an HTTPS server. The normal solution to this is to use a "reverse proxy" setup, where a general web server handles HTTP and HTTP requests (to port 80 & 443 respectively), then passes on the request to the back-end application (in this case Spothole). nginx is a common choice for this general web server.

To set up nginx as a reverse proxy that sits in front of Youth Map, first ensure it's installed e.g. `sudo apt install nginx`, and enabled e.g. `sudo systemd enable nginx`.

Create a file at `/etc/nginx/sites-available/` called `youthmap`. Give it the following contents, replacing `youthmap.com` with the domain name on which you want to run Youth Map. If you changed the port on which Youth Map runs, update that on the "proxy_pass" line too.

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

Test that your nginx config isn't broken using `nginx -t`. If it works, restart nginx with `sudo systemctl restart nginx`.

If you haven't already done so, set up a DNS entry to make sure requests for your domain name end up at the server that's running Youth Map.

You should now be able to access the web interface by going to the domain from your browser.

Once that's working, [install certbot](https://certbot.eff.org/instructions?ws=nginx&os=snap) onto your server. Run it as root, and when prompted pick your domain name from the list. After a few seconds, it should successfully provision a certificate and modify your nginx config files automatically. You should then be able to access the site via HTTPS.
