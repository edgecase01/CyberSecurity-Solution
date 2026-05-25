"""Gmail API helpers using per-user OAuth credentials."""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build

from config import Settings
from models import User

GMAIL_SCOPES = ["https://mail.google.com/"]


@dataclass
class GmailMessageContent:
    id: str
    thread_id: str
    subject: str
    body: str
    sender: str


def build_gmail_credentials(user: User, settings: Settings) -> Credentials:
    if not user.google_refresh_token:
        raise ValueError("User has no google_refresh_token. Re-authenticate with Google OAuth.")

    credentials = Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.gmail_client_id,
        client_secret=settings.gmail_client_secret,
        scopes=GMAIL_SCOPES,
    )

    if credentials.expired or not credentials.valid:
        credentials.refresh(Request())

    return credentials


def build_gmail_service(
    user: User,
    settings: Settings,
    credentials: Credentials | None = None,
) -> Resource:
    creds = credentials or build_gmail_credentials(user, settings)
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def list_unread_message_ids(service: Resource, max_results: int = 5) -> list[dict[str, str]]:
    response = (
        service.users()
        .messages()
        .list(userId="me", q="is:unread", maxResults=max_results)
        .execute()
    )
    return response.get("messages", [])


def _decode_body_data(data: str) -> str:
    padded = data + "=" * (-len(data) % 4)
    raw = base64.urlsafe_b64decode(padded.encode("utf-8"))
    return raw.decode("utf-8", errors="replace")


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def _extract_body_from_payload(payload: dict[str, Any]) -> str:
    mime_type = payload.get("mimeType", "")
    body = payload.get("body", {})

    if body.get("data"):
        decoded = _decode_body_data(body["data"])
        if mime_type == "text/html":
            return _strip_html(decoded)
        return decoded

    parts = payload.get("parts", [])
    plain_parts: list[str] = []
    html_parts: list[str] = []

    for part in parts:
        part_mime = part.get("mimeType", "")
        if part_mime.startswith("multipart/"):
            nested = _extract_body_from_payload(part)
            if nested:
                plain_parts.append(nested)
            continue
        if part_mime == "text/plain":
            plain_parts.append(_extract_body_from_payload(part))
        elif part_mime == "text/html":
            html_parts.append(_extract_body_from_payload(part))

    if plain_parts:
        return "\n".join(part for part in plain_parts if part).strip()
    if html_parts:
        return "\n".join(part for part in html_parts if part).strip()
    return ""


def get_message_content(service: Resource, message_id: str) -> GmailMessageContent:
    message = (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )
    payload = message.get("payload", {})
    headers = {header["name"]: header["value"] for header in payload.get("headers", [])}

    return GmailMessageContent(
        id=message["id"],
        thread_id=message.get("threadId", ""),
        subject=headers.get("Subject", "(no subject)"),
        body=_extract_body_from_payload(payload),
        sender=headers.get("From", ""),
    )


def quarantine_message(service: Resource, message_id: str, *, use_spam_label: bool = True) -> dict[str, Any]:
    """
    Remove from INBOX and mark as SPAM (default) or TRASH.
    """
    add_label = "SPAM" if use_spam_label else "TRASH"
    return (
        service.users()
        .messages()
        .modify(
            userId="me",
            id=message_id,
            body={
                "removeLabelIds": ["INBOX", "UNREAD"],
                "addLabelIds": [add_label],
            },
        )
        .execute()
    )
