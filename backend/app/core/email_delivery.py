import json
import os
import smtplib
from collections.abc import Callable
from contextlib import closing
from email.message import EmailMessage
from email.utils import formataddr, parseaddr
from http.client import HTTPException, HTTPSConnection

SENDER_NAME = "SCHOLWARD Academy"


class EmailConfigurationError(RuntimeError):
    pass


class EmailDeliveryError(RuntimeError):
    pass


def send_over_https(host: str, path: str, headers: dict[str, str], payload: dict) -> None:
    with closing(HTTPSConnection(host, timeout=10)) as connection:
        connection.request(
            "POST",
            path,
            body=json.dumps(payload),
            headers={**headers, "Content-Type": "application/json"},
        )
        with connection.getresponse() as response:
            if not 200 <= response.status < 300:
                raise EmailDeliveryError("Email provider rejected the request")


def configured_email_sender() -> Callable[[str, str, str], None]:
    brevo_key = (os.getenv("BREVO_API_KEY") or "").strip()
    brevo_from = (os.getenv("BREVO_FROM") or "").strip()
    resend_key = (os.getenv("RESEND_API_KEY") or "").strip()
    resend_from = (os.getenv("RESEND_FROM") or "").strip()
    smtp_host = os.getenv("SMTP_HOST")
    smtp_from = os.getenv("SMTP_FROM")
    smtp_username = (os.getenv("SMTP_USERNAME") or "").strip()
    smtp_password = "".join((os.getenv("SMTP_PASSWORD") or "").split())
    if brevo_key or brevo_from:
        configured = bool(brevo_key and brevo_from)
        sender = brevo_from
    elif resend_key or resend_from:
        configured = bool(resend_key and resend_from)
        sender = resend_from
    else:
        configured = bool(smtp_host and smtp_from and smtp_username and smtp_password)
        sender = smtp_from
    if not configured:
        raise EmailConfigurationError("Email delivery is not configured")
    _, sender_email = parseaddr(sender or "")
    if not sender_email:
        raise EmailConfigurationError("Invalid email sender")
    sender_header = formataddr((SENDER_NAME, sender_email))

    def send(recipient: str, subject: str, body: str) -> None:
        try:
            if brevo_key:
                send_over_https(
                    "api.brevo.com",
                    "/v3/smtp/email",
                    {"api-key": brevo_key},
                    {
                        "sender": {"name": SENDER_NAME, "email": sender_email},
                        "to": [{"email": recipient}],
                        "subject": subject,
                        "textContent": body,
                    },
                )
            elif resend_key:
                send_over_https(
                    "api.resend.com",
                    "/emails",
                    {"Authorization": f"Bearer {resend_key}"},
                    {"from": sender_header, "to": [recipient], "subject": subject, "text": body},
                )
            else:
                message = EmailMessage()
                message["Subject"] = subject
                message["To"] = recipient
                message["From"] = sender_header
                message.set_content(body)
                port = int(os.getenv("SMTP_PORT", "587"))
                smtp_client = smtplib.SMTP_SSL if port == 465 else smtplib.SMTP
                with smtp_client(smtp_host, port, timeout=10) as smtp:
                    if port != 465:
                        smtp.starttls()
                    smtp.login(smtp_username, smtp_password)
                    smtp.send_message(message)
        except (OSError, HTTPException, ValueError):
            raise EmailDeliveryError("Unable to send email") from None

    return send
