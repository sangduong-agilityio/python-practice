"""
app/services/email_service.py
------------------------------
Email sending utilities used as FastAPI BackgroundTasks.

FastAPI BackgroundTasks run AFTER the HTTP response is sent to the client.
This means the user gets a fast response (e.g. "registered!") without
waiting for the email to be delivered.

In production you'd use a proper task queue (Celery, ARQ), but
BackgroundTasks is perfect for simple use cases.
"""

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_welcome_email(email: str, username: str) -> None:
    """
    Send a welcome email to a newly registered user.

    This runs in the background after the /auth/register response is sent.

    Args:
        email    : Recipient email address.
        username : User's display name for personalization.
    """
    # In a real app, use aiosmtplib or a service like SendGrid / Mailgun.
    # Here we log instead to keep the setup simple for beginners.
    logger.info(
        "📧 [Background] Sending welcome email to %s (%s)", username, email
    )

    # Uncomment to actually send emails (requires SMTP settings in .env):
    #
    # import aiosmtplib
    # from email.mime.text import MIMEText
    #
    # message = MIMEText(f"Welcome to the Task Manager, {username}!")
    # message["Subject"] = "Welcome!"
    # message["From"] = settings.SMTP_USER
    # message["To"] = email
    #
    # await aiosmtplib.send(
    #     message,
    #     hostname=settings.SMTP_HOST,
    #     port=settings.SMTP_PORT,
    #     username=settings.SMTP_USER,
    #     password=settings.SMTP_PASSWORD,
    #     start_tls=True,
    # )


async def send_task_assigned_email(
    assignee_email: str,
    assignee_username: str,
    task_title: str,
    project_title: str,
) -> None:
    """
    Notify a user that a task has been assigned to them.

    Args:
        assignee_email    : Recipient email.
        assignee_username : Recipient's display name.
        task_title        : Title of the assigned task.
        project_title     : Name of the project containing the task.
    """
    logger.info(
        "📧 [Background] Notifying %s about assigned task '%s' in project '%s'",
        assignee_email,
        task_title,
        project_title,
    )
    # Add real SMTP logic here following the same pattern as above
