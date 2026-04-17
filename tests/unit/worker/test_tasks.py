"""
Unit tests for email worker tasks.

Verifies that sending logic respects env configurations and correctly routes to smtp.
"""

from unittest.mock import MagicMock, patch
import pytest

from app.worker.tasks import send_task_assigned_email, send_welcome_email

def test_send_welcome_email_skips_when_smtp_not_configured():
    """Make sure smtp is wholly avoided if the user/password config is blank."""
    with (
        patch("app.worker.tasks.settings") as mock_settings,
        patch("app.worker.tasks.smtplib.SMTP") as mock_smtp,
    ):
        mock_settings.SMTP_USER = ""
        from app.worker import tasks as task_module
        task_module._smtp_send("user@example.com", "Welcome", "<p>Hi</p>")
        mock_smtp.assert_not_called()

def test_send_welcome_email_sends_when_smtp_configured():
    """Verify that the underlying smtp lib actually gets triggered with full config."""
    with (
        patch("app.worker.tasks.settings") as mock_settings,
        patch("app.worker.tasks.smtplib.SMTP") as mock_smtp,
    ):
        mock_settings.SMTP_USER = "sender@example.com"
        mock_settings.SMTP_PASSWORD = "app_password"
        mock_settings.SMTP_HOST = "smtp.gmail.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.EMAILS_FROM_NAME = "Task Manager"

        smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = smtp_instance

        from app.worker import tasks as task_module
        task_module._smtp_send("recipient@example.com", "Test Subject", "<p>Body</p>")

        smtp_instance.starttls.assert_called_once()
        smtp_instance.login.assert_called_once_with("sender@example.com", "app_password")
        smtp_instance.sendmail.assert_called_once()

def test_send_welcome_email_does_not_raise_on_smtp_error():
    """Swallow smtp errors gracefully so the celery worker doesn't hard crash."""
    with (
        patch("app.worker.tasks.settings") as mock_settings,
        patch("app.worker.tasks.smtplib.SMTP") as mock_smtp,
    ):
        mock_settings.SMTP_USER = "sender@example.com"
        mock_settings.SMTP_PASSWORD = "pw"
        mock_settings.SMTP_HOST = "smtp.gmail.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.EMAILS_FROM_NAME = "App"

        mock_smtp.side_effect = ConnectionRefusedError("SMTP unavailable")

        from app.worker import tasks as task_module
        # this shouldn't raise out since we swallowed it
        task_module._smtp_send("user@example.com", "Subject", "<p>Hi</p>")


def test_send_task_assigned_email_skips_when_smtp_not_configured():
    """Task assigned email shouldn't fire if smtp lacks config."""
    with (
        patch("app.worker.tasks.settings") as mock_settings,
        patch("app.worker.tasks.smtplib.SMTP") as mock_smtp,
    ):
        mock_settings.SMTP_USER = ""
        from app.worker import tasks as task_module
        task_module._smtp_send("assignee@example.com", "Task assigned", "<p>You got a task</p>")
        mock_smtp.assert_not_called()

def test_send_task_assigned_email_sends_with_correct_recipient():
    """Task assignments should actually go to the assigned person."""
    with (
        patch("app.worker.tasks.settings") as mock_settings,
        patch("app.worker.tasks.smtplib.SMTP") as mock_smtp,
    ):
        mock_settings.SMTP_USER = "sender@example.com"
        mock_settings.SMTP_PASSWORD = "pw"
        mock_settings.SMTP_HOST = "smtp.gmail.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.EMAILS_FROM_NAME = "App"

        smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = smtp_instance

        from app.worker import tasks as task_module
        task_module._smtp_send("assignee@example.com", "Task: Fix bug", "<p>You got it</p>")

        call_args = smtp_instance.sendmail.call_args
        # verify routing
        assert "sender@example.com" == call_args[0][0]
        assert "assignee@example.com" == call_args[0][1]
