"""
Google Calendar tool — creates real calendar events via OAuth2.

Uses the token saved by app.config.gmail_auth (gmail_token.json).
Returns a clear error if not authorised — no simulation fallback.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseTool

logger    = logging.getLogger(__name__)
OWNER_EMAIL     = "jcw.loong@gmail.com"
CREDENTIALS_DIR = Path(__file__).parent.parent.parent.parent / "credentials"
TOKEN_FILE      = CREDENTIALS_DIR / "gmail_token.json"
SCOPES          = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
]


class CalendarTool(BaseTool):
    def __init__(self):
        self._service = None

    @property
    def name(self) -> str:
        return "create_calendar_event"

    @property
    def description(self) -> str:
        return (
            f"Create a real Google Calendar event. Organiser is always {OWNER_EMAIL}. "
            "Generates a Google Meet link and sends email invites to all attendees."
        )

    def _get_service(self):
        if self._service is not None:
            return self._service

        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        if not TOKEN_FILE.exists():
            raise FileNotFoundError(
                f"OAuth token not found at {TOKEN_FILE}. "
                "Run: python -m app.config.gmail_auth"
            )

        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                TOKEN_FILE.write_text(creds.to_json())
                logger.info("Calendar OAuth token refreshed")
            else:
                raise RuntimeError(
                    "OAuth token is invalid. "
                    "Delete credentials/gmail_token.json and run: "
                    "python -m app.config.gmail_auth"
                )

        if not any("calendar" in s for s in (creds.scopes or [])):
            raise PermissionError(
                "Calendar scope not granted. Delete credentials/gmail_token.json "
                "and re-run: python -m app.config.gmail_auth"
            )

        self._service = build("calendar", "v3", credentials=creds)
        logger.info("Google Calendar service ready")
        return self._service

    def execute(
        self,
        summary: str,
        start_datetime: str,
        end_datetime: str,
        description: str = "",
        attendees: Optional[List[str]] = None,
        timezone: str = "America/New_York",
        **kwargs,
    ) -> Dict[str, Any]:

        ok, missing = self.validate_params(
            ["summary", "start_datetime", "end_datetime"],
            {"summary": summary, "start_datetime": start_datetime, "end_datetime": end_datetime},
        )
        if not ok:
            return self._err(f"Missing required fields: {missing}")

        try:
            service       = self._get_service()
            attendee_list = [{"email": OWNER_EMAIL, "organizer": True}]
            for email in (attendees or []):
                if email.lower() != OWNER_EMAIL.lower():
                    attendee_list.append({"email": email})

            created = service.events().insert(
                calendarId="primary",
                body={
                    "summary":     summary,
                    "description": description or "Scheduled via Customer Support Assistant",
                    "start":       {"dateTime": start_datetime, "timeZone": timezone},
                    "end":         {"dateTime": end_datetime,   "timeZone": timezone},
                    "attendees":   attendee_list,
                    "conferenceData": {
                        "createRequest": {
                            "requestId":            f"csa-{start_datetime.replace(':', '-')}",
                            "conferenceSolutionKey": {"type": "hangoutsMeet"},
                        }
                    },
                    "reminders": {
                        "useDefault": False,
                        "overrides":  [
                            {"method": "email", "minutes": 24 * 60},
                            {"method": "popup", "minutes": 15},
                        ],
                    },
                },
                conferenceDataVersion=1,
                sendUpdates="all",
            ).execute()

            meet_link = next(
                (ep["uri"] for ep in created.get("conferenceData", {}).get("entryPoints", [])
                 if ep.get("entryPointType") == "video"),
                None,
            )

            logger.info(f"Calendar event created: {created.get('id')} — {summary}")
            return self._ok({
                "event_id":   created.get("id"),
                "event_link": created.get("htmlLink"),
                "meet_link":  meet_link,
                "summary":    created.get("summary"),
                "start":      created.get("start"),
                "end":        created.get("end"),
                "attendees":  [a["email"] for a in created.get("attendees", [])],
                "status":     "confirmed",
            })

        except (FileNotFoundError, PermissionError, RuntimeError) as exc:
            return self._err(str(exc))
        except Exception as exc:
            logger.error(f"Calendar API error: {exc}")
            return self._err(f"Failed to create calendar event: {exc}")


calendar_tool = CalendarTool()
