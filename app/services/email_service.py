"""
Email sending.

These functions are queued as background tasks so the HTTP response
goes out immediately and the SMTP round-trip happens after. If SMTP_USER
is blank (the default in development) the function logs and returns --
no crash, no scary traceback.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

log = logging.getLogger(__name__)


def _send(to: str, subject: str, body_html: str) -> None:
    """Synchronously send an HTML email via SMTP.

    This should generally be called within a background task to prevent
    blocking the main async event loop. If SMTP_USER is not configured,
    it simply logs the action and returns safely.

    Args:
        to: Recipient email address.
        subject: The subject line of the email.
        body_html: The HTML string body of the email.
    """
    if not settings.SMTP_USER:
        log.info("SMTP not configured, skipping email to %s: %s", to, subject)
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.SMTP_USER}>"
        msg["To"] = to
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, to, msg.as_string())

        log.info("Email sent to %s: %s", to, subject)
    except Exception:
        # Background tasks must not crash the worker. Log and move on.
        log.exception("Failed to send email to %s", to)


def send_welcome(to: str, username: str) -> None:
    """Dispatch a welcome email to a newly registered user.

    Args:
        to: The user's email address.
        username: The user's display name.
    """
    _send(
        to=to,
        subject=f"Welcome, {username}",
        body_html=f"<p>Hi {username}, your account is ready.</p>",
    )


def send_task_assigned(to: str, username: str, task_title: str) -> None:
    """Notify a user that a new task has been assigned to them.

    Args:
        to: The assignee's email address.
        username: The assignee's display name.
        task_title: The title of the task.
    """
    _send(
        to=to,
        subject=f"Task assigned to you: {task_title}",
        body_html=f"<p>Hi {username}, the task <strong>{task_title}</strong> was assigned to you.</p>",
    )
