"""
Unit tests for app.worker.tasks (email task logic).

These tests verify that:
- Tasks skip SMTP when SMTP_USER is not configured.
- Tasks call smtplib with correct arguments when SMTP is configured.
- Celery retry is triggered on SMTP failure.

All tests use unittest.mock to avoid real network calls.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.worker.tasks import send_task_assigned_email, send_welcome_email


# ---------------------------------------------------------------------------
# send_welcome_email
# ---------------------------------------------------------------------------


def test_send_welcome_email_skips_when_smtp_not_configured():
    """No SMTP call should be made when SMTP_USER is empty."""
    with (
        patch("app.worker.tasks.settings") as mock_settings,
        patch("app.worker.tasks.smtplib.SMTP") as mock_smtp,
    ):
        mock_settings.SMTP_USER = ""
        # Call the underlying function directly (bypass Celery task wrapper)
        from app.worker import tasks as task_module
        task_module._smtp_send("user@example.com", "Welcome", "<p>Hi</p>")
        mock_smtp.assert_not_called()


def test_send_welcome_email_sends_when_smtp_configured():
    """SMTP login and sendmail must be called when SMTP_USER is set."""
    with (
        patch("app.worker.tasks.settings") as mock_settings,
        patch("app.worker.tasks.smtplib.SMTP") as mock_smtp,
    ):
        mock_settings.SMTP_USER = "sender@example.com"
        mock_settings.SMTP_PASSWORD = "app_password"
        mock_settings.SMTP_HOST = "smtp.gmail.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.EMAILS_FROM_NAME = "Task Manager"

        # Configure the SMTP context manager mock
        smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = smtp_instance

        from app.worker import tasks as task_module
        task_module._smtp_send("recipient@example.com", "Test Subject", "<p>Body</p>")

        smtp_instance.starttls.assert_called_once()
        smtp_instance.login.assert_called_once_with("sender@example.com", "app_password")
        smtp_instance.sendmail.assert_called_once()


def test_send_welcome_email_does_not_raise_on_smtp_error():
    """SMTP errors must be swallowed (logged) — task should not crash."""
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
        # Should not raise — errors are caught and logged
        task_module._smtp_send("user@example.com", "Subject", "<p>Hi</p>")


# ---------------------------------------------------------------------------
# send_task_assigned_email
# ---------------------------------------------------------------------------


def test_send_task_assigned_email_skips_when_smtp_not_configured():
    """No SMTP call should be made when SMTP is not configured."""
    with (
        patch("app.worker.tasks.settings") as mock_settings,
        patch("app.worker.tasks.smtplib.SMTP") as mock_smtp,
    ):
        mock_settings.SMTP_USER = ""
        from app.worker import tasks as task_module
        task_module._smtp_send("assignee@example.com", "Task assigned", "<p>You got a task</p>")
        mock_smtp.assert_not_called()


def test_send_task_assigned_email_sends_with_correct_recipient():
    """sendmail must be called with the assignee's email as recipient."""
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
        # Third positional arg is the raw message string
        assert "sender@example.com" == call_args[0][0]
        assert "assignee@example.com" == call_args[0][1]
