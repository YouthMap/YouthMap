import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def notify_admins_user_added_station(db, new_station):
    """Send mail to all administrators, letting them know that a user has created a new station which is now awaiting
    their approval."""
    subject = "New station awaiting approval"
    html_content = f"""\
    <html>
      <body>
        <p>A new station has been added to Youth Map by a user. This is now awaiting your approval. Please review the details below and either approve or delete the station. Please note that this email has been sent to all administrators of the site.</p>
        <p>Callsign: <strong>{ new_station.callsign }</strong></p>
        <p>Name: <strong>{ new_station.club_name }</strong></p>
        { ("<p>Event: <strong>" + new_station.event.name + "</strong></p>") if hasattr(new_station, "event") else "" }
        { ("<p>Type: <strong>" + new_station.type.name + "</strong></p>") if hasattr(new_station, "type") else "" }
        { ("<p>Meeting: " + new_station.meeting_when + "</p>") if hasattr(new_station, "meeting_when") else "" }
        { ("<p>Meeting: " + new_station.meeting_where + "</p>") if hasattr(new_station, "meeting_where") else "" }
        { ("<p>Notes: " + new_station.notes + "</p>") if new_station.notes else "" }
        { ("<p>Email: " + new_station.email + "</p>") if new_station.email else "" }
        { ("<p>Phone: " + new_station.phone_number + "</p>") if new_station.phone_number else "" }
        { ("<p>Website: <a href='" + new_station.website_url + "'>" + new_station.website_url + "</a></p>") if new_station.website_url else "" }
        { ("<p>Social media: <a href='" + new_station.social_media_url + "'>" + new_station.social_media_url + "</a></p>") if new_station.social_media_url else "" }
        { ("<p>QRZ page: <a href='" + new_station.qrz_url + "'>" + new_station.qrz_url + "</a></p>") if new_station.qrz_url else "" }
        <p><br/><a href="TODO" style="font-size: 1.2em; color: white; text-decoration: none; background-color: green; padding: 0.4em; border-radius: 0.3em;">Approve</a>
        <a href="TODO" style="font-size: 1.2em; color: white; text-decoration: none; background-color: #0d6efd; padding: 0.4em; border-radius: 0.3em;">Review</a>
        <a href="TODO" style="font-size: 1.2em; color: white; text-decoration: none; background-color: red; padding: 0.4em; border-radius: 0.3em;">Delete</a></p>
      </body>
    </html>
    """

    return send_mail_to_all_admins(db, subject, html_content)


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
            # Get email addresses for all admins
            recipients = [x.email for x in db.get_all_users()]

            # Create the message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = config.mail_sender
            msg["To"] = ", ".join(recipients)
            msg.attach(MIMEText("This is an HTML email. Please use an HTML-capable email client to view it.", "plain"))
            msg.attach(MIMEText(html_content, "html"))

            # Send the message
            with smtplib.SMTP(config.mail_server, 587) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(config.mail_sender, config.mail_password)
                server.sendmail(config.mail_sender, recipients, msg.as_string())
                logging.info("Sent mail.")
                return True

        except Exception as e:
            logging.error("Failed to send mail", e)
            return False

    else:
        return False
