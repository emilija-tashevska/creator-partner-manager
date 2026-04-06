"""
One-time OAuth consent flow for Gmail API access.

Usage:
    1. Go to Google Cloud Console → APIs & Services → Credentials
    2. Create an OAuth 2.0 Client ID (Desktop app type)
    3. Download the JSON and save it as `client_secret.json` in this directory
    4. Run: python -m scripts.gmail_oauth
    5. Complete the browser consent flow
    6. Copy the printed refresh_token into your .env file as GMAIL_REFRESH_TOKEN
"""

import json
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]
CLIENT_SECRET_PATH = Path(__file__).parent / "client_secret.json"


def main():
    if not CLIENT_SECRET_PATH.exists():
        print(f"Error: {CLIENT_SECRET_PATH} not found.")
        print()
        print("To set up Gmail OAuth:")
        print("1. Go to https://console.cloud.google.com/apis/credentials")
        print("2. Create an OAuth 2.0 Client ID (type: Desktop application)")
        print("3. Download the JSON file")
        print(f"4. Save it as: {CLIENT_SECRET_PATH}")
        print("5. Run this script again")
        sys.exit(1)

    print("Starting Gmail OAuth consent flow...")
    print("A browser window will open for you to authorize access.")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CLIENT_SECRET_PATH), scopes=SCOPES
    )
    creds = flow.run_local_server(port=8090, open_browser=True)

    print()
    print("=" * 60)
    print("SUCCESS! Add these to your .env file:")
    print("=" * 60)
    print()

    with open(CLIENT_SECRET_PATH) as f:
        client_config = json.load(f)
        installed = client_config.get("installed", client_config.get("web", {}))

    print(f'GMAIL_CLIENT_ID={installed.get("client_id", "")}')
    print(f'GMAIL_CLIENT_SECRET={installed.get("client_secret", "")}')
    print(f"GMAIL_REFRESH_TOKEN={creds.refresh_token}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
