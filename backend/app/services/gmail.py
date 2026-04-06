import base64
import logging
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.config import settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]


class GmailService:
    """Creates Gmail drafts using OAuth2 credentials."""

    def __init__(self, credentials: Credentials):
        self.service = build("gmail", "v1", credentials=credentials)

    def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        attachment_path: str | None = None,
    ) -> str:
        """
        Create a Gmail draft and return its draft ID.
        Optionally attaches a PDF file.
        """
        if attachment_path:
            message = self._build_multipart_message(to, subject, body, attachment_path)
        else:
            message = self._build_simple_message(to, subject, body)

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        draft = (
            self.service.users()
            .drafts()
            .create(userId="me", body={"message": {"raw": raw}})
            .execute()
        )
        draft_id = draft["id"]
        logger.info(f"Created Gmail draft {draft_id} to {to}")
        return draft_id

    def _build_simple_message(self, to: str, subject: str, body: str) -> MIMEText:
        message = MIMEText(body, "plain")
        message["to"] = to
        message["subject"] = subject
        return message

    def _build_multipart_message(
        self, to: str, subject: str, body: str, attachment_path: str
    ) -> MIMEMultipart:
        message = MIMEMultipart()
        message["to"] = to
        message["subject"] = subject
        message.attach(MIMEText(body, "plain"))

        path = Path(attachment_path)
        if path.exists():
            with open(path, "rb") as f:
                attachment = MIMEApplication(f.read(), _subtype="pdf")
                attachment.add_header(
                    "Content-Disposition", "attachment", filename=path.name
                )
                message.attach(attachment)
        else:
            logger.warning(f"Attachment not found: {attachment_path}")

        return message


def load_credentials_from_config() -> Credentials:
    """
    Build OAuth2 credentials from the settings (env vars).
    MVP: single Gmail account configured via environment variables.
    """
    if not settings.gmail_refresh_token:
        raise ValueError(
            "Gmail refresh token not configured. "
            "Run `python -m scripts.gmail_oauth` to set up Gmail access."
        )

    creds = Credentials(
        token=None,
        refresh_token=settings.gmail_refresh_token,
        client_id=settings.gmail_client_id,
        client_secret=settings.gmail_client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return creds


def get_gmail_service() -> GmailService:
    """Factory for the Gmail service using env-based credentials."""
    creds = load_credentials_from_config()
    return GmailService(credentials=creds)
