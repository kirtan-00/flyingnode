import os
import requests

API = "https://api.brevo.com/v3"


def send(to_email: str, subject: str, html: str) -> dict:
    r = requests.post(
        f"{API}/smtp/email",
        headers={
            "api-key": os.environ["BREVO_API_KEY"],
            "content-type": "application/json",
            "accept": "application/json",
        },
        json={
            "sender": {
                "email": os.environ.get("BREVO_SENDER_EMAIL", "REDACTED_EMAIL"),
                "name": os.environ.get("BREVO_SENDER_NAME", "flyingnode"),
            },
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html,
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json()
