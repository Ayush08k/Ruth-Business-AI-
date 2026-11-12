"""
Ruth Email Integration
- Read and classify emails via Gmail API
- Draft replies in owner's style
- Send formatted HTML daily reports
- OAuth2 authentication (your own Google account)
"""
import base64
import json
import os
import re
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from rich.console import Console

from ruth.config import config

console = Console()

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


class EmailManager:
    """
    Gmail integration for Ruth.
    Reads, classifies, drafts, and sends emails on your behalf.
    """

    def __init__(self):
        self.service = None
        self._connected = False
        self._setup_gmail()

    def _setup_gmail(self):
        """Initialize Gmail API connection"""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            token_path = Path(config.GMAIL_TOKEN_FILE)
            creds = None

            if token_path.exists():
                creds = Credentials.from_authorized_user_file(str(token_path), GMAIL_SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    cred_file = Path(config.GMAIL_CREDENTIALS_FILE)
                    if not cred_file.exists():
                        console.print("[yellow]⚠️  Gmail credentials.json not found. Email features disabled.[/yellow]")
                        console.print("[dim]  → To enable: Download credentials.json from Google Cloud Console[/dim]")
                        return

                    flow = InstalledAppFlow.from_client_secrets_file(str(cred_file), GMAIL_SCOPES)
                    creds = flow.run_local_server(port=0)

                token_path.parent.mkdir(parents=True, exist_ok=True)
                token_path.write_text(creds.to_json())

            self.service = build("gmail", "v1", credentials=creds)
            self._connected = True
            console.print("[green]✅ Gmail connected[/green]")

        except ImportError:
            console.print("[yellow]⚠️  Google API libraries not installed. Run: pip install google-api-python-client google-auth-oauthlib[/yellow]")
        except Exception as e:
            console.print(f"[yellow]⚠️  Gmail setup failed: {e}[/yellow]")

    def is_connected(self) -> bool:
        return self._connected and self.service is not None

    def get_unread_emails(self, max_results: int = 20) -> list[dict]:
        """Fetch unread emails"""
        if not self.is_connected():
            return []
        try:
            result = self.service.users().messages().list(
                userId="me", q="is:unread", maxResults=max_results
            ).execute()
            messages = result.get("messages", [])
            emails = []
            for m in messages:
                email = self._parse_email(m["id"])
                if email:
                    emails.append(email)
            return emails
        except Exception as e:
            console.print(f"[red]Error fetching emails: {e}[/red]")
            return []

    def _parse_email(self, msg_id: str) -> Optional[dict]:
        """Parse a Gmail message into a readable dict"""
        try:
            msg = self.service.users().messages().get(
                userId="me", id=msg_id, format="full"
            ).execute()
            headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
            body = self._get_body(msg["payload"])
            return {
                "id": msg_id,
                "from": headers.get("From", "Unknown"),
                "subject": headers.get("Subject", "(No Subject)"),
                "date": headers.get("Date", ""),
                "body": body[:1000],  # First 1000 chars
                "snippet": msg.get("snippet", ""),
            }
        except Exception as e:
            console.print(f"[dim red]Error parsing email {msg_id}: {e}[/dim red]")
            return None

    def _get_body(self, payload: dict) -> str:
        """Extract email body text"""
        if "body" in payload and payload["body"].get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        return ""

    def get_summary(self) -> str:
        """Get a formatted summary of unread emails"""
        if not self.is_connected():
            return "Email not configured. Please add credentials.json from Google Cloud Console."

        emails = self.get_unread_emails(10)
        if not emails:
            return "No unread emails. 📭 Your inbox is clean!"

        lines = [f"📧 You have {len(emails)} unread email(s):\n"]
        for i, email in enumerate(emails[:5], 1):
            sender = email["from"].split("<")[0].strip()
            lines.append(f"{i}. From: {sender}")
            lines.append(f"   Subject: {email['subject']}")
            lines.append(f"   Preview: {email['snippet'][:80]}...\n")

        if len(emails) > 5:
            lines.append(f"...and {len(emails) - 5} more.")

        return "\n".join(lines)

    def send_email(self, to: str, subject: str, html_body: str, plain_body: str = "") -> bool:
        """Send an email"""
        if not self.is_connected():
            console.print("[yellow]⚠️  Email not connected[/yellow]")
            return False
        try:
            msg = MIMEMultipart("alternative")
            msg["to"] = to
            msg["subject"] = subject
            if plain_body:
                msg.attach(MIMEText(plain_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            self.service.users().messages().send(
                userId="me", body={"raw": raw}
            ).execute()
            console.print(f"[green]✅ Email sent to {to}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Failed to send email: {e}[/red]")
            return False

    def send_daily_report(self, report_data: dict = None) -> str:
        """Send formatted HTML daily report to owner"""
        if not config.REPORT_EMAIL:
            return "Report email address not configured."

        html = self._build_report_html(report_data or {})
        date_str = datetime.now().strftime("%d %B %Y")
        subject = f"📊 Ruth Daily Report — {date_str}"

        if self.send_email(config.REPORT_EMAIL, subject, html):
            return f"Daily report sent to {config.REPORT_EMAIL}"
        return "Failed to send report."

    def _build_report_html(self, data: dict) -> str:
        """Build beautiful HTML report email"""
        date_str = datetime.now().strftime("%A, %d %B %Y, %I:%M %p")
        email_count = data.get("email_count", "N/A")
        urgent_count = data.get("urgent_count", 0)
        website_status = "✅ ONLINE" if data.get("site_up", True) else "🚨 OFFLINE"
        tasks_pending = data.get("tasks_pending", 0)
        insights = data.get("insights", "No insights yet.")

        return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
    .container {{ max-width: 600px; margin: auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
    .header {{ background: linear-gradient(135deg, #1a1a2e, #16213e); color: white; padding: 30px; text-align: center; }}
    .header h1 {{ margin: 0; font-size: 28px; letter-spacing: 2px; }}
    .header p {{ margin: 5px 0 0; opacity: 0.8; }}
    .section {{ padding: 20px 30px; border-bottom: 1px solid #eee; }}
    .section h2 {{ color: #1a1a2e; font-size: 16px; margin: 0 0 10px; }}
    .metric {{ display: inline-block; background: #f8f9fa; border-radius: 8px; padding: 12px 20px; margin: 5px; text-align: center; }}
    .metric .value {{ font-size: 24px; font-weight: bold; color: #1a1a2e; }}
    .metric .label {{ font-size: 12px; color: #666; }}
    .alert-urgent {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px 15px; border-radius: 4px; margin: 5px 0; }}
    .status-ok {{ color: #28a745; font-weight: bold; }}
    .status-err {{ color: #dc3545; font-weight: bold; }}
    .footer {{ background: #1a1a2e; color: rgba(255,255,255,0.6); text-align: center; padding: 15px; font-size: 12px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>⚡ RUTH</h1>
      <p>Daily Business Report — {date_str}</p>
    </div>

    <div class="section">
      <h2>📊 Summary</h2>
      <div class="metric"><div class="value">{email_count}</div><div class="label">Emails</div></div>
      <div class="metric"><div class="value">{urgent_count}</div><div class="label">Urgent</div></div>
      <div class="metric"><div class="value">{tasks_pending}</div><div class="label">Tasks Pending</div></div>
    </div>

    <div class="section">
      <h2>🌐 Website Status</h2>
      <p class="{'status-ok' if data.get('site_up', True) else 'status-err'}">{website_status}</p>
      <p>Response time: {data.get('response_time', 'N/A')}</p>
    </div>

    <div class="section">
      <h2>📧 Email Highlights</h2>
      {self._format_email_highlights(data.get('email_highlights', []))}
    </div>

    <div class="section">
      <h2>💡 Ruth's Insights</h2>
      <p>{insights}</p>
    </div>

    <div class="footer">
      Generated by Ruth AI — Your Personal Business Assistant
    </div>
  </div>
</body>
</html>
"""

    def _format_email_highlights(self, highlights: list) -> str:
        if not highlights:
            return "<p>No email highlights.</p>"
        items = "".join([
            f'<div class="alert-urgent"><strong>{h.get("from","")}</strong>: {h.get("subject","")}</div>'
            for h in highlights[:5]
        ])
        return items

    def draft_reply(self, to: str, subject: str, context: str) -> str:
        """Return a draft reply (actual sending handled by brain tool)"""
        return f"Draft for {to} re: '{subject}': [Ruth will compose based on context: {context}]"

