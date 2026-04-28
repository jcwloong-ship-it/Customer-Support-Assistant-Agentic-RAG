"""
Gmail tool — sends real emails from jcw.loong@gmail.com via OAuth2.

Returns a clear error if not authorised — no simulation fallback.
Run: python -m app.config.gmail_auth  for one-time setup.
"""

import base64
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

from .base import BaseTool

logger           = logging.getLogger(__name__)
SENDER_EMAIL     = "jcw.loong@gmail.com"
DEFAULT_RECIPIENT = "jcw.loong@gmail.com"


class EmailTool(BaseTool):
    def __init__(self):
        self._service = None

    @property
    def name(self) -> str:
        return "send_email"

    @property
    def description(self) -> str:
        return (
            f"Send a real email from {SENDER_EMAIL} via Gmail. "
            f"Defaults to sending to {DEFAULT_RECIPIENT} if no recipient is specified."
        )

    def _get_service(self):
        if self._service is None:
            from app.config.gmail_auth import get_gmail_service
            self._service = get_gmail_service()
            logger.info(f"Gmail service ready for {SENDER_EMAIL}")
        return self._service

    def execute(
        self,
        to: Optional[str] = None,
        subject: str = "",
        body: str = "",
        **kwargs,
    ) -> Dict[str, Any]:
        to = to or DEFAULT_RECIPIENT

        ok, missing = self.validate_params(
            ["subject", "body"],
            {"subject": subject, "body": body},
        )
        if not ok:
            return self._err(f"Missing required params: {missing}")

        try:
            service = self._get_service()

            msg            = MIMEMultipart()
            msg["to"]      = to
            msg["from"]    = SENDER_EMAIL
            msg["subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            raw  = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            sent = service.users().messages().send(
                userId="me", body={"raw": raw}
            ).execute()

            logger.info(f"Email sent: id={sent.get('id')} to={to}")
            return self._ok({
                "message_id": sent.get("id"),
                "thread_id":  sent.get("threadId"),
                "to":         to,
                "subject":    subject,
                "from":       SENDER_EMAIL,
                "body":       body,
                "status":     "sent",
            })

        except FileNotFoundError:
            msg = (
                "Gmail OAuth credentials not found. "
                "Run: python -m app.config.gmail_auth"
            )
            logger.error(msg)
            return self._err(msg)

        except Exception as exc:
            logger.error(f"Gmail send failed: {exc}")
            return self._err(f"Failed to send email: {exc}")


email_tool = EmailTool()
