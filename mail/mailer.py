import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def notify_admins_user_added_station(db, new_station):
    """Send mail to all administrators, letting them know that a user has created a new station which is now awaiting
    their approval."""

    site_base_url = db.get_config().base_url
    station_type = "perm" if hasattr(new_station, "type") else "temp"
    subject = "[Youth Map] New station awaiting approval"
    html_content = f"""\
    <html>
      <body>
        <p>A new station has been added to Youth Map by a user. This is now awaiting your approval. Please review the details below and either approve or delete the station. Please note that this email has been sent to all administrators of the site.</p>

        {get_station_details_for_email(new_station)}

        <p><br/><a href="{site_base_url}/admin/handleemaillink?action=approve&type={station_type}&id={new_station.id}" style="font-size: 1.2em; color: white; text-decoration: none; background-color: green; padding: 0.4em; border-radius: 0.3em;">Approve</a>
        <a href="{site_base_url}/admin/station/{station_type}/{new_station.id}" style="font-size: 1.2em; color: white; text-decoration: none; background-color: #0d6efd; padding: 0.4em; border-radius: 0.3em; margin-left: 0.5em;">Review</a>
        <a href="{site_base_url}/admin/handleemaillink?action=delete&type={station_type}&id={new_station.id}" style="font-size: 1.2em; color: white; text-decoration: none; background-color: red; padding: 0.4em; border-radius: 0.3em; margin-left: 0.5em;">Delete</a></p>
      </body>
    </html>
    """

    return send_mail_to_all_admins(db, subject, html_content)


def notify_admins_user_deleted_station(db, station):
    """Send mail to all administrators, letting them know that a user has deleted a station."""

    subject = "[Youth Map] Station deleted"
    html_content = f"""\
    <html>
      <body>
        <p>A station has been deleted from Youth Map by a user. There is nothing required from you at this point, this is just for your information. The details of the deleted station were as follows.</p>

        {get_station_details_for_email(station)}
        
      </body>
    </html>
    """

    return send_mail_to_all_admins(db, subject, html_content)


def notify_admins_user_updated_station(db, station):
    """Generic function that sends mail to all administrators when a user updates an event. The form it takes and the
    actions that are available depend on whether the station is already approved or not, so first we check that, then
    delegate to another function as necessary."""

    if station.approved:
        notify_admins_user_updated_approved_station(db, station)
    else:
        notify_admins_user_updated_unapproved_station(db, station)


def notify_admins_user_updated_approved_station(db, station):
    """Send mail to all administrators, letting them know that a user has updated an existing station which is still
    approved and visible, but has been shown to admins as a check to prevent griefing."""

    site_base_url = db.get_config().base_url
    station_type = "perm" if hasattr(station, "type") else "temp"
    subject = "[Youth Map] Information updated for approved station"
    html_content = f"""\
    <html>
      <body>
        <p>An existing station has been updated by a user. It is still approved and live in the system. Please review the details below ensure that it has not been maliciously edited. Please note that this email has been sent to all administrators of the site.</p>
        
        {get_station_details_for_email(station)}
        
        <p><br/><a href="{site_base_url}/admin/station/{station_type}/{station.id}" style="font-size: 1.2em; color: white; text-decoration: none; background-color: #0d6efd; padding: 0.4em; border-radius: 0.3em;">Review</a>
        <a href="{site_base_url}/admin/handleemaillink?action=unapprove&type={station_type}&id={station.id}" style="font-size: 1.2em; color: white; text-decoration: none; background-color: red; padding: 0.4em; border-radius: 0.3em; margin-left: 0.5em;">Unapprove</a>
        <a href="{site_base_url}/admin/handleemaillink?action=delete&type={station_type}&id={station.id}" style="font-size: 1.2em; color: white; text-decoration: none; background-color: red; padding: 0.4em; border-radius: 0.3em; margin-left: 0.5em;">Delete</a></p>
      </body>
    </html>
    """

    return send_mail_to_all_admins(db, subject, html_content)


def notify_admins_user_updated_unapproved_station(db, station):
    """Send mail to all administrators, letting them know that a user has updated a station which is still waiting in
    the approval queue, but now has new details."""

    site_base_url = db.get_config().base_url
    station_type = "perm" if hasattr(station, "type") else "temp"
    subject = "[Youth Map] Information updated for station in approval queue"
    html_content = f"""\
    <html>
      <body>
        <p>A station in the approval queue has been updated by a user. It is still waiting for admin approval, we are just updating you to show the new information. Please review the details below and either approve or delete the station. Please note that this email has been sent to all administrators of the site.</p>
        
        {get_station_details_for_email(station)}
        
        <p><br/><a href="{site_base_url}/admin/handleemaillink?action=approve&type={station_type}&id={station.id}" style="font-size: 1.2em; color: white; text-decoration: none; background-color: green; padding: 0.4em; border-radius: 0.3em;">Approve</a>
        <a href="{site_base_url}/admin/station/{station_type}/{station.id}" style="font-size: 1.2em; color: white; text-decoration: none; background-color: #0d6efd; padding: 0.4em; border-radius: 0.3em; margin-left: 0.5em;">Review</a>
        <a href="{site_base_url}/admin/handleemaillink?action=delete&type={station_type}&id={station.id}" style="font-size: 1.2em; color: white; text-decoration: none; background-color: red; padding: 0.4em; border-radius: 0.3em; margin-left: 0.5em;">Delete</a></p>
      </body>
    </html>
    """

    return send_mail_to_all_admins(db, subject, html_content)


def get_station_details_for_email(station):
    """Get a string providing a description of the station, in HTML format, for email. This is common between "user
    created a station" and "user updated a station" so has been extracted into a separate method."""

    return f"""\
        <p>Callsign: <strong>{station.callsign}</strong></p>
        <p>Name: <strong>{station.club_name}</strong></p>
        {("<p>Event: <strong>" + station.event.name + "</strong></p>") if hasattr(station, "event") else ""}
        {("<p>Type: <strong>" + station.type.name + "</strong></p>") if hasattr(station, "type") else ""}
        {("<p>Meeting: " + station.meeting_when + "</p>") if hasattr(station, "meeting_when") else ""}
        {("<p>Meeting: " + station.meeting_where + "</p>") if hasattr(station, "meeting_where") else ""}
        {("<p>Notes: " + station.notes + "</p>") if station.notes else ""}
        {("<p>Email: " + station.email + "</p>") if station.email else ""}
        {("<p>Phone: " + station.phone_number + "</p>") if station.phone_number else ""}
        {("<p>Website: <a href='" + station.website_url + "'>" + station.website_url + "</a></p>") if station.website_url else ""}
        {("<p>Social media: <a href='" + station.social_media_url + "'>" + station.social_media_url + "</a></p>") if station.social_media_url else ""}
        {("<p>QRZ page: <a href='" + station.qrz_url + "'>" + station.qrz_url + "</a></p>") if station.qrz_url else ""}
    """


def send_mail_to_all_admins(db, subject, html_content):
    """Sends mail to all administrators with the provided HTML content. (If sending mail is disabled on this site, this
    will be ignored.) The first parameter provided must be the database object, which we need to use to look up SMTP
    config and administrator emails. The second and third parameters are the subject line and content of the mail."""

    recipients = [x.email for x in db.get_all_users()]
    return send_mail(db, recipients, subject, html_content)


def send_mail(db, recipients, subject, html_content):
    """Sends mail to the recipient(s) with the provided HTML content. (If sending mail is disabled on this site, this
    will be ignored.) The first parameter provided must be the database object, which we need to use to look up SMTP
    config and administrator emails. The second parameter is the list of recipients, which should be an array of
    strings. The third and fourth parameters are the subject line and content of the mail."""

    # Get config, and check we are actually configured to send mail
    config = db.get_config()
    if config.enable_mail:
        try:
            # Create the message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = config.mail_sender
            msg["To"] = ", ".join(recipients)
            msg.attach(MIMEText("This is an HTML email. Please use an HTML-capable email client to view it.", "plain"))
            msg.attach(MIMEText(html_content, "html"))

            # Send the message
            with smtplib.SMTP(config.mail_server_host, config.mail_server_port) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(config.mail_username, config.mail_password)
                server.sendmail(config.mail_sender, recipients, msg.as_string())
                logging.info("Sent mail.")
                return True

        except Exception as e:
            logging.error("Failed to send mail", e)
            return False

    else:
        return False
