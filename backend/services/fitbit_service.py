# Business logic for Fitbit API interactions.
# Handles the OAuth 2.0 authorization flow and fetching health data
# (heart rate, sleep, breathing rate, exercise logs).

import requests
from datetime import date
from sqlalchemy.orm import Session
from config import settings
from models.health_snapshot import HealthSnapshot

# In-memory token storage for now. Replace with DB-backed storage for production.
_fitbit_tokens: dict = {}

FITBIT_AUTH_URL = "https://www.fitbit.com/oauth2/authorize"
FITBIT_TOKEN_URL = "https://api.fitbit.com/oauth2/token"
FITBIT_API_BASE = "https://api.fitbit.com/1/user/-"


def get_auth_url() -> str:
    """Build the Fitbit OAuth authorization URL to redirect the user to."""
    params = {
        "response_type": "code",
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.FITBIT_REDIRECT_URI,
        "scope": "heartrate sleep respiratory_rate activity",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{FITBIT_AUTH_URL}?{query}"


def exchange_code_for_token(code: str) -> dict:
    """Exchange the OAuth authorization code for access + refresh tokens."""
    response = requests.post(
        FITBIT_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.FITBIT_REDIRECT_URI,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
        },
    )
    response.raise_for_status()
    tokens = response.json()
    _fitbit_tokens["access_token"] = tokens["access_token"]
    _fitbit_tokens["refresh_token"] = tokens["refresh_token"]
    return tokens


def _get_headers() -> dict:
    """Build authorization headers for Fitbit API requests."""
    return {"Authorization": f"Bearer {_fitbit_tokens.get('access_token', '')}"}


def fetch_heart_rate(target_date: date) -> dict:
    """Fetch heart rate data for a specific day."""
    url = f"{FITBIT_API_BASE}/activities/heart/date/{target_date}/1d.json"
    response = requests.get(url, headers=_get_headers())
    response.raise_for_status()
    return response.json()


def fetch_sleep(target_date: date) -> dict:
    """Fetch sleep data for a specific day."""
    url = f"{FITBIT_API_BASE}/sleep/date/{target_date}.json"
    response = requests.get(url, headers=_get_headers())
    response.raise_for_status()
    return response.json()


def fetch_breathing_rate(target_date: date) -> dict:
    """Fetch breathing rate data for a specific day."""
    url = f"{FITBIT_API_BASE}/br/date/{target_date}.json"
    response = requests.get(url, headers=_get_headers())
    response.raise_for_status()
    return response.json()


def save_health_snapshot(target_date: date, data: dict, db: Session) -> HealthSnapshot:
    """Persist a day's health data to the database. Updates if already exists."""
    existing = db.query(HealthSnapshot).filter(HealthSnapshot.date == target_date).first()

    if existing:
        for key, value in data.items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing

    snapshot = HealthSnapshot(date=target_date, **data)
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot
