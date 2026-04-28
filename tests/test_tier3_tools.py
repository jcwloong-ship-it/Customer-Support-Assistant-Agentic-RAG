"""
Tier 3 — Tool Execution & Security Tests
==========================================
Validates that tools handle auth failures, API errors, and bad input
gracefully — returning structured error dicts rather than crashing,
and that the UI always sees a clean error message rather than a raw
Python traceback.
"""

import base64
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.agents.tools.base import BaseTool
from app.agents.tools.calendar_tool import CalendarTool, OWNER_EMAIL
from app.agents.tools.email_tool import EmailTool, SENDER_EMAIL, DEFAULT_RECIPIENT
from app.agents.tools.registry import execute_tool


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_calendar_tool() -> CalendarTool:
    tool = CalendarTool()
    tool._service = None
    return tool


def _make_email_tool() -> EmailTool:
    tool = EmailTool()
    tool._service = None
    return tool


VALID_CAL_ARGS = {
    "summary":        "Product Demo",
    "start_datetime": "2026-05-20T10:00:00",
    "end_datetime":   "2026-05-20T10:45:00",
    "attendees":      ["client@example.com"],
    "timezone":       "America/New_York",
}

VALID_EMAIL_ARGS = {
    "to":      "alice@example.com",
    "subject": "Meeting Confirmation",
    "body":    "Your meeting is confirmed.",
}


# ── Tests: OAuth credential handling ──────────────────────────────────────────

class TestOAuthTokenHandling:

    def test_calendar_missing_token_returns_error_dict(self):
        """If gmail_token.json does not exist, the tool must return a structured
        error — not raise an unhandled FileNotFoundError."""
        tool = _make_calendar_tool()

        with patch("pathlib.Path.exists", return_value=False):
            result = tool.execute(**VALID_CAL_ARGS)

        assert result["success"] is False
        assert result["result"]  is None
        assert "token" in result["error"].lower() or "oauth" in result["error"].lower(), (
            f"Error message should mention token/oauth, got: {result['error']}"
        )

    def test_email_missing_credentials_returns_error_dict(self):
        """Missing OAuth credentials must return a structured error, not a crash."""
        tool = _make_email_tool()

        with patch("app.config.gmail_auth.get_gmail_service",
                   side_effect=FileNotFoundError("OAuth credentials not found")):
            result = tool.execute(**VALID_EMAIL_ARGS)

        assert result["success"] is False
        assert result["error"]   is not None
        assert "oauth" in result["error"].lower() or "credentials" in result["error"].lower()

    def test_expired_token_triggers_silent_refresh(self, tmp_path):
        """When the saved token is expired but has a refresh_token, the tool
        must silently refresh it without showing an error to the user."""
        tool = _make_calendar_tool()

        mock_creds = MagicMock()
        mock_creds.valid         = False
        mock_creds.expired       = True
        mock_creds.refresh_token = "valid-refresh-token"
        # Provide the calendar scope so the scope-check passes
        mock_creds.scopes = [
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/calendar",
        ]

        def _refresh(_request):
            mock_creds.valid = True  # simulate token becoming valid

        mock_creds.refresh.side_effect = _refresh

        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.write_text"), \
             patch("google.oauth2.credentials.Credentials.from_authorized_user_file",
                   return_value=mock_creds), \
             patch("google.auth.transport.requests.Request"), \
             patch("googleapiclient.discovery.build", return_value=MagicMock()) as mock_build:

            service = tool._get_service()

        mock_creds.refresh.assert_called_once()
        mock_build.assert_called_once_with("calendar", "v3", credentials=mock_creds)
        assert service is not None

    def test_calendar_scope_missing_returns_permission_error(self, tmp_path):
        """If the saved token lacks the calendar scope, the tool must return
        a clear PermissionError rather than crashing mid-execution."""
        tool       = _make_calendar_tool()
        token_file = tmp_path / "gmail_token.json"
        token_file.write_text("{}")

        mock_creds = MagicMock()
        mock_creds.valid  = True
        mock_creds.scopes = ["https://www.googleapis.com/auth/gmail.send"]  # no calendar scope

        with patch("pathlib.Path.exists", return_value=True), \
             patch("google.oauth2.credentials.Credentials.from_authorized_user_file",
                   return_value=mock_creds):
            result = tool.execute(**VALID_CAL_ARGS)

        assert result["success"] is False
        assert "calendar" in result["error"].lower() or "scope" in result["error"].lower(), (
            f"Expected scope/calendar in error, got: {result['error']}"
        )


# ── Tests: API error handling ──────────────────────────────────────────────────

class TestAPIErrorHandling:

    def _patched_calendar_service(self):
        """Return a mock Calendar service and a CalendarTool that uses it."""
        tool            = _make_calendar_tool()
        mock_service    = MagicMock()
        tool._service   = mock_service
        return tool, mock_service

    def _patched_email_service(self):
        tool           = _make_email_tool()
        mock_service   = MagicMock()
        tool._service  = mock_service
        return tool, mock_service

    def test_calendar_api_error_returns_structured_error(self):
        """A googleapiclient.errors.HttpError must be caught and returned as
        a structured error dict — never as a raw traceback."""
        from googleapiclient.errors import HttpError
        from unittest.mock import MagicMock

        tool, svc = self._patched_calendar_service()

        mock_resp = MagicMock()
        mock_resp.status = 400
        mock_resp.reason = "Bad Request"
        svc.events.return_value.insert.return_value.execute.side_effect = HttpError(
            resp=mock_resp, content=b"invalid attendee"
        )

        result = tool.execute(**VALID_CAL_ARGS)

        assert result["success"] is False
        assert result["result"]  is None
        assert result["error"]   is not None
        # Error message must be a clean string, not a repr of an exception object
        assert isinstance(result["error"], str)

    def test_gmail_api_error_returns_structured_error(self):
        """A Gmail send failure must be caught and returned as a structured
        error — never propagated as an unhandled exception."""
        tool, svc = self._patched_email_service()

        svc.users.return_value.messages.return_value.send.return_value.execute.side_effect = (
            Exception("Invalid recipient address")
        )

        result = tool.execute(**VALID_EMAIL_ARGS)

        assert result["success"] is False
        assert isinstance(result["error"], str), "Error must be a string, not an exception object"

    def test_invalid_email_address_captured_not_raised(self):
        """Providing a malformed email should result in a structured error
        dict, never a raised exception reaching the Streamlit UI."""
        tool, svc = self._patched_email_service()

        svc.users.return_value.messages.return_value.send.return_value.execute.side_effect = (
            Exception("400: Invalid 'To' address: not-an-email")
        )

        # Should NOT raise
        result = tool.execute(to="not-an-email", subject="Test", body="Hello")

        assert result["success"] is False
        assert result["result"]  is None
        assert "failed" in result["error"].lower() or "error" in result["error"].lower()


# ── Tests: Input validation ────────────────────────────────────────────────────

class TestInputValidation:

    def test_calendar_missing_summary_returns_error(self):
        tool   = _make_calendar_tool()
        result = tool.execute(
            summary="",
            start_datetime="2026-05-20T10:00:00",
            end_datetime="2026-05-20T10:45:00",
        )
        assert result["success"] is False
        assert "summary" in result["error"].lower() or "missing" in result["error"].lower()

    def test_calendar_missing_start_datetime_returns_error(self):
        tool   = _make_calendar_tool()
        result = tool.execute(
            summary="Demo",
            start_datetime="",
            end_datetime="2026-05-20T10:45:00",
        )
        assert result["success"] is False

    def test_email_missing_subject_returns_error(self):
        tool   = _make_email_tool()
        result = tool.execute(to="a@b.com", subject="", body="hello")
        assert result["success"] is False
        assert "subject" in result["error"].lower() or "missing" in result["error"].lower()

    def test_email_missing_body_returns_error(self):
        tool   = _make_email_tool()
        result = tool.execute(to="a@b.com", subject="Test", body="")
        assert result["success"] is False

    def test_email_defaults_to_owner_inbox_when_no_recipient(self):
        """Omitting 'to' should default to DEFAULT_RECIPIENT, not raise a KeyError."""
        tool, svc = MagicMock(), MagicMock()
        email_tool = _make_email_tool()
        email_tool._service = svc

        sent_mock = MagicMock()
        sent_mock.get.side_effect = lambda k: {"id": "msg_001", "threadId": "thr_001"}.get(k)
        svc.users.return_value.messages.return_value.send.return_value.execute.return_value = {
            "id": "msg_001", "threadId": "thr_001"
        }

        result = email_tool.execute(subject="Test", body="Hello, owner!")

        # Should succeed and default to the owner's inbox
        assert result["success"] is True
        assert result["result"]["to"] == DEFAULT_RECIPIENT

    def test_calendar_owner_always_in_attendees(self):
        """The owner email must always be in the attendee list regardless of
        what the LLM provides."""
        tool, svc = _make_calendar_tool(), MagicMock()
        tool._service = svc

        # Simulate a successful API response
        svc.events.return_value.insert.return_value.execute.return_value = {
            "id":             "evt_789",
            "htmlLink":       "https://cal.google.com/evt_789",
            "summary":        "Demo",
            "conferenceData": {"entryPoints": []},
            "start":          {"dateTime": "2026-05-20T10:00:00"},
            "end":            {"dateTime": "2026-05-20T10:45:00"},
            "attendees":      [
                {"email": OWNER_EMAIL},
                {"email": "client@example.com"},
            ],
        }

        result = tool.execute(
            summary="Demo",
            start_datetime="2026-05-20T10:00:00",
            end_datetime="2026-05-20T10:45:00",
            attendees=["client@example.com"],
        )

        assert result["success"] is True
        assert OWNER_EMAIL in result["result"]["attendees"]


# ── Tests: Tool registry ───────────────────────────────────────────────────────

class TestToolRegistry:

    def test_known_tool_dispatched_correctly(self):
        """execute_tool must route to the right tool and return its result."""
        with patch("app.agents.tools.registry.email_tool") as mock_email:
            mock_email.name = "send_email"
            mock_email.execute.return_value = {
                "success": True, "result": {"status": "sent"}, "error": None
            }

            from app.agents.tools import registry
            registry._REGISTRY["send_email"] = mock_email

            result = execute_tool("send_email",
                                  to="a@b.com", subject="Hi", body="Hello")

        assert result["success"] is True

    def test_unknown_tool_returns_error_dict(self):
        """An unregistered tool name must return a structured error, not raise."""
        result = execute_tool("non_existent_tool", arg="value")
        assert result["success"] is False
        assert "unknown tool" in result["error"].lower()

    def test_tool_error_does_not_propagate_as_exception(self):
        """BaseTool._err must return a structured dict so errors never reach
        the Streamlit UI as raw tracebacks. Test directly on BaseTool._err."""
        from app.agents.tools.email_tool import EmailTool
        tool = EmailTool()

        # _err must return a dict, not raise
        result = tool._err("Something went badly wrong")

        assert isinstance(result, dict), "_err must return a dict"
        assert result["success"] is False
        assert result["result"]  is None
        assert "Something went badly wrong" in result["error"]


# ── Tests: Email content integrity ────────────────────────────────────────────

class TestEmailContentIntegrity:

    def test_email_body_sent_unchanged(self):
        """The exact body text provided must reach the Gmail API without
        modification or truncation."""
        tool          = _make_email_tool()
        mock_service  = MagicMock()
        tool._service = mock_service

        mock_service.users.return_value.messages.return_value.send.return_value.execute.return_value = {
            "id": "msg_x", "threadId": "thr_x"
        }

        body = "This is the exact body. Special chars: é, ñ, 中文, 🎉"
        tool.execute(to="a@b.com", subject="Test", body=body)

        # The Gmail API receives a base64url-encoded MIME message.
        # The text body is itself base64-encoded as a MIME part inside the envelope.
        # We decode the outer MIME message, collect the inner base64 body lines,
        # and decode those to verify the body arrived intact.
        call_args = mock_service.users.return_value.messages.return_value.send.call_args
        raw_b64   = call_args.kwargs["body"]["raw"]
        mime_text = base64.urlsafe_b64decode(raw_b64 + "==").decode("utf-8", errors="replace")

        inner_lines, collecting = [], False
        for line in mime_text.splitlines():
            if "Content-Transfer-Encoding: base64" in line:
                collecting = True
                continue
            if collecting:
                stripped = line.strip()
                if stripped.startswith("--"):
                    break
                if stripped:
                    inner_lines.append(stripped)

        inner_decoded = base64.b64decode("".join(inner_lines) + "==").decode("utf-8", errors="replace")
        assert body in inner_decoded, (
            f"Email body was altered.\nExpected: {body!r}\nGot: {inner_decoded!r}"
        )

    def test_from_address_is_always_sender_email(self):
        """The From header must always be SENDER_EMAIL regardless of input."""
        tool          = _make_email_tool()
        mock_service  = MagicMock()
        tool._service = mock_service

        mock_service.users.return_value.messages.return_value.send.return_value.execute.return_value = {
            "id": "msg_y", "threadId": "thr_y"
        }

        result = tool.execute(to="anyone@example.com", subject="Hi", body="Hello")

        assert result["result"]["from"] == SENDER_EMAIL

    def test_sender_email_constant_matches_gmail_auth(self):
        """SENDER_EMAIL in email_tool must match the value in gmail_auth."""
        from app.config.gmail_auth import SENDER_EMAIL as AUTH_SENDER
        assert SENDER_EMAIL == AUTH_SENDER, (
            f"Mismatch: email_tool uses '{SENDER_EMAIL}', "
            f"gmail_auth uses '{AUTH_SENDER}'"
        )
