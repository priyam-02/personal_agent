#!/usr/bin/env python3
"""
Run this ONCE on your local machine (not inside Docker) to get a Gmail refresh token.

Steps:
  1. Go to https://console.cloud.google.com/
  2. Create a project (or use existing)
  3. Enable the Gmail API
  4. Go to APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID
  5. Application type: "Desktop app"
  6. Download the JSON → rename to client_secret.json → place next to this script
  7. Run: python setup_gmail.py
  8. Copy the refresh token into your .env file
"""

import json
import sys
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Install required package: pip install google-auth-oauthlib")
    sys.exit(1)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

SECRET_FILE = Path("client_secret.json")

def main():
    if not SECRET_FILE.exists():
        print(f"❌ {SECRET_FILE} not found!")
        print("Download your OAuth credentials from Google Cloud Console")
        print("and save them as client_secret.json in this directory.")
        sys.exit(1)

    print("🔑 Starting Gmail OAuth2 flow...")
    print("A browser window will open. Sign in and grant access.\n")

    flow = InstalledAppFlow.from_client_secrets_file(str(SECRET_FILE), SCOPES)
    creds = flow.run_local_server(port=8090, prompt="consent", access_type="offline")

    print("\n✅ Authorization successful!\n")
    print("=" * 60)
    print(f"GMAIL_REFRESH_TOKEN={creds.refresh_token}")
    print("=" * 60)
    print(f"\nClient ID:     {creds.client_id}")
    print(f"Client Secret: {creds.client_secret}")
    print(f"\n👆 Copy the GMAIL_REFRESH_TOKEN line into your .env file")


if __name__ == "__main__":
    main()
