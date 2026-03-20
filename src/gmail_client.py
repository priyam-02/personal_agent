from __future__ import annotations

import base64
import email
import logging
import os
import re
from email.mime.text import MIMEText
from dataclasses import dataclass

import httplib2
from google.oauth2.credentials import Credentials
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build

logger = logging.getLogger("nemoclaw.gmail")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


@dataclass
class EmailMessage:
    id: str
    thread_id: str
    sender: str
    sender_email: str
    to: str
    subject: str
    snippet: str
    body_text: str
    body_html: str
    date: str
    labels: list[str]
    category: str


class GmailClient:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=SCOPES,
        )
        # Use proxy if available (required in NemoClaw sandbox)
        proxy_url = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        if proxy_url:
            proxy_info = httplib2.proxy_info_from_url(proxy_url)
            http = httplib2.Http(proxy_info=proxy_info)
        else:
            http = httplib2.Http()
        authorized_http = AuthorizedHttp(creds, http=http)
        self.service = build("gmail", "v1", http=authorized_http)
        self.user_email = self._get_user_email()
        logger.info(f"Gmail client initialized for {self.user_email}")

    def _get_user_email(self) -> str:
        profile = self.service.users().getProfile(userId="me").execute()
        return profile.get("emailAddress", "unknown")

    def fetch_new_messages(
        self,
        label_ids: list[str] | None = None,
        max_results: int = 10,
        history_id: str | None = None,
    ) -> list[EmailMessage]:
        """Fetch recent unread messages."""
        try:
            if label_ids is None:
                label_ids = ["INBOX", "UNREAD"]

            results = (
                self.service.users()
                .messages()
                .list(
                    userId="me",
                    labelIds=label_ids,
                    maxResults=max_results,
                )
                .execute()
            )

            messages = results.get("messages", [])
            if not messages:
                return []

            emails = []
            for msg_stub in messages:
                try:
                    em = self._fetch_full_message(msg_stub["id"])
                    if em:
                        emails.append(em)
                except Exception as e:
                    logger.warning(f"Failed to fetch message {msg_stub['id']}: {e}")

            return emails

        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return []

    def _fetch_full_message(self, msg_id: str) -> EmailMessage | None:
        msg = (
            self.service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )

        headers = {h["name"].lower(): h["value"] for h in msg["payload"]["headers"]}

        sender_raw = headers.get("from", "Unknown")
        sender_name, sender_email = self._parse_sender(sender_raw)

        body_text, body_html = self._extract_body(msg["payload"])

        # Detect category from labels
        labels = msg.get("labelIds", [])
        category = "primary"
        for label in labels:
            if label.startswith("CATEGORY_"):
                category = label.replace("CATEGORY_", "").lower()

        return EmailMessage(
            id=msg["id"],
            thread_id=msg.get("threadId", ""),
            sender=sender_name or sender_email,
            sender_email=sender_email,
            to=headers.get("to", ""),
            subject=headers.get("subject", "(no subject)"),
            snippet=msg.get("snippet", ""),
            body_text=body_text[:4000],  # Truncate for API limits
            body_html=body_html[:4000],
            date=headers.get("date", ""),
            labels=labels,
            category=category,
        )

    def _parse_sender(self, raw: str) -> tuple[str, str]:
        match = re.match(r'"?([^"<]*)"?\s*<?([^>]*)>?', raw)
        if match:
            name = match.group(1).strip().strip('"')
            addr = match.group(2).strip() or raw
            return name, addr
        return "", raw

    def _extract_body(self, payload: dict) -> tuple[str, str]:
        text_body = ""
        html_body = ""

        if "parts" in payload:
            for part in payload["parts"]:
                mime = part.get("mimeType", "")
                if mime == "text/plain" and not text_body:
                    text_body = self._decode_part(part)
                elif mime == "text/html" and not html_body:
                    html_body = self._decode_part(part)
                elif "parts" in part:
                    # Nested multipart
                    t, h = self._extract_body(part)
                    if not text_body:
                        text_body = t
                    if not html_body:
                        html_body = h
        else:
            mime = payload.get("mimeType", "")
            data = self._decode_part(payload)
            if mime == "text/plain":
                text_body = data
            elif mime == "text/html":
                html_body = data

        return text_body, html_body

    def _decode_part(self, part: dict) -> str:
        body = part.get("body", {})
        data = body.get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        return ""

    def send_reply(
        self, thread_id: str, to: str, subject: str, body: str, message_id: str = ""
    ) -> str:
        """Send a reply within a thread."""
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = (
            subject if subject.lower().startswith("re:") else f"Re: {subject}"
        )
        if message_id:
            message["In-Reply-To"] = message_id
            message["References"] = message_id

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        sent = (
            self.service.users()
            .messages()
            .send(userId="me", body={"raw": raw, "threadId": thread_id})
            .execute()
        )

        logger.info(f"Reply sent: {sent['id']}")
        return sent["id"]

    def mark_as_read(self, msg_id: str):
        self.service.users().messages().modify(
            userId="me",
            id=msg_id,
            body={"removeLabelIds": ["UNREAD"]},
        ).execute()
