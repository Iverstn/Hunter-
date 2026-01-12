from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.settings import settings


def send_email(subject: str, html_body: str, text_body: str, recipient: str | None = None) -> bool:
    if not all(
        [settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.smtp_sender]
    ):
        return False
    to_addr = recipient or settings.default_email_recipient
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_sender
    msg["To"] = to_addr

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.sendmail(settings.smtp_sender, [to_addr], msg.as_string())
    return True
