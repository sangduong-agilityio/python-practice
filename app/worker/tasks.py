"""
Celery task definitions.

All background work (email sending) is defined here as Celery tasks so the
HTTP response is returned immediately and heavy I/O happens asynchronously
in a dedicated worker process. This file must NOT import FastAPI internals
to keep the worker dependency footprint minimal.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import structlog

from app.core.config import settings
from app.worker.celery_app import celery_app

log = structlog.get_logger(__name__)
stdlib_log = logging.getLogger(__name__)


def _smtp_send(to: str, subject: str, body_html: str) -> None:
    """Send an HTML email synchronously via SMTP.

    This is a private helper called only from within Celery tasks, which run
    in a separate worker process, so blocking SMTP I/O does not affect the
    ASGI event loop.

    If SMTP_USER is not configured the call is a no-op: it logs the skipped
    action and returns, which prevents test environments from crashing.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body_html: Full HTML body content.
    """
    if not settings.SMTP_USER:
        log.info("SMTP not configured -- skipping email to %s: %s", to, subject)
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
        # Tasks must not crash permanently on email failure. Celery retry
        # logic handles transient SMTP errors; permanent errors are logged.
        log.exception("Failed to send email to %s", to)


@celery_app.task(
    name="send_welcome_email",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_welcome_email(self, user_email: str, username: str, request_id: str = "unknown") -> None:
    """Send a welcome email to a newly registered user.

    Triggered asynchronously after a successful POST /auth/register. Uses
    Celery retry on unexpected failures so transient SMTP errors do not
    silently drop the email.

    Args:
        user_email: The new user's email address.
        username: The new user's display name.
        request_id: Request ID for tracing (from HTTP request context).
    """
    try:
        log.info(
            "background_task_started",
            task_name="send_welcome_email",
            task_id=self.request.id,
            request_id=request_id,
            email=user_email,
        )

        _smtp_send(
            to=user_email,
            subject=f"Welcome, {username}",
            body_html=(
                f"<p>Hi {username},</p>"
                "<p>Your Task Management account is ready. "
                "Start by creating your first project.</p>"
            ),
        )

        log.info(
            "background_task_completed",
            task_name="send_welcome_email",
            task_id=self.request.id,
            request_id=request_id,
            email=user_email,
            status="success",
        )
    except Exception as exc:
        log.error(
            "background_task_failed",
            task_name="send_welcome_email",
            task_id=self.request.id,
            request_id=request_id,
            email=user_email,
            error=str(exc),
            retry_count=self.request.retries,
        )
        raise self.retry(exc=exc) from exc


@celery_app.task(
    name="send_task_assigned_email",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_task_assigned_email(
    self,
    assignee_email: str,
    task_title: str,
    assigner_username: str,
    request_id: str = "unknown",
) -> None:
    """Notify a user by email that a task has been assigned to them.

    Triggered asynchronously after a successful PATCH /tasks/{id}/assign.

    Args:
        assignee_email: Email address of the user being assigned the task.
        task_title: Title of the assigned task.
        assigner_username: Username of the person who performed the assignment.
        request_id: Request ID for tracing (from HTTP request context).
    """
    try:
        log.info(
            "background_task_started",
            task_name="send_task_assigned_email",
            task_id=self.request.id,
            request_id=request_id,
            task_title=task_title,
            assignee_email=assignee_email,
        )

        _smtp_send(
            to=assignee_email,
            subject=f"Task assigned to you: {task_title}",
            body_html=(
                f"<p>Hi,</p>"
                f"<p><strong>{assigner_username}</strong> assigned the task "
                f"<strong>{task_title}</strong> to you.</p>"
            ),
        )

        log.info(
            "background_task_completed",
            task_name="send_task_assigned_email",
            task_id=self.request.id,
            request_id=request_id,
            task_title=task_title,
            assignee_email=assignee_email,
            status="success",
        )
    except Exception as exc:
        log.error(
            "background_task_failed",
            task_name="send_task_assigned_email",
            task_id=self.request.id,
            request_id=request_id,
            task_title=task_title,
            assignee_email=assignee_email,
            error=str(exc),
            retry_count=self.request.retries,
        )
        raise self.retry(exc=exc) from exc
