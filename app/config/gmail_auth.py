"""
Gmail + Google Calendar OAuth2 authentication.

Handles the one-time browser consent flow and automatic token refresh
for both the Gmail send and Calendar scopes.

One-time setup:
  1. Go to console.cloud.google.com and create a project
  2. Enable Gmail API and Google Calendar API
  3. OAuth consent screen → External → add your email as a test user
  4. Credentials → OAuth 2.0 Client ID → Desktop App → download JSON
  5. Save the downloaded file as credentials/oauth_credentials.json
  6. Run: python -m app.config.gmail_auth
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR        = Path(__file__).parent.parent.parent
CREDENTIALS_DIR = BASE_DIR / "credentials"
OAUTH_FILE      = CREDENTIALS_DIR / "oauth_credentials.json"
TOKEN_FILE      = CREDENTIALS_DIR / "gmail_token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
]

SENDER_EMAIL = "jcw.loong@gmail.com"


def get_gmail_service():
    """
    Return an authenticated Gmail API service.

    Loads the saved token on subsequent calls and silently refreshes
    it when expired. Opens a browser for consent only on the first run.

    Raises:
        FileNotFoundError: oauth_credentials.json is missing.
    """
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        logger.info("Loaded saved OAuth token")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            logger.info("OAuth token refreshed")
        else:
            if not OAUTH_FILE.exists():
                raise FileNotFoundError(
                    f"OAuth credentials not found at {OAUTH_FILE}.\n"
                    "See credentials/SETUP.md for setup instructions."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(OAUTH_FILE), SCOPES)
            creds = flow.run_local_server(port=0, open_browser=True)
            logger.info("OAuth consent completed")

        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(creds.to_json())
        logger.info(f"Token saved to {TOKEN_FILE}")

    return build("gmail", "v1", credentials=creds)


def check_auth_status() -> dict:
    """
    Return current auth state without opening a browser.
    Used by the Streamlit sidebar to show the Gmail status badge.
    """
    status = {
        "oauth_file_exists": OAUTH_FILE.exists(),
        "token_exists":      TOKEN_FILE.exists(),
        "token_valid":       False,
        "sender_email":      SENDER_EMAIL,
    }

    if TOKEN_FILE.exists():
        try:
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
            status["token_valid"] = creds.valid or bool(creds.refresh_token)
        except Exception:
            pass

    return status


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(f"\nStarting OAuth flow for {SENDER_EMAIL} …")
    get_gmail_service()
    print(f"\n✅ Authenticated successfully!")
    print(f"   Sender  : {SENDER_EMAIL}")
    print(f"   Token   : {TOKEN_FILE}")
    print(f"   Scopes  : gmail.send, calendar")
    print(f"\n   Run: python -m streamlit run streamlit_app.py\n")
