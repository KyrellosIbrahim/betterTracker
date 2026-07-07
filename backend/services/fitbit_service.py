# Business logic for Google Health API interactions (formerly Fitbit).
# Handles the Google OAuth 2.0 authorization flow and fetching health data
# (heart rate, sleep, breathing rate, exercise logs) via the Health API v4.

import requests
from datetime import date, timedelta
from sqlalchemy.orm import Session
from urllib.parse import urlencode
from config import settings
from models.health_snapshot import HealthSnapshot

# In-memory token storage for now. Replace with DB-backed storage for production.
_google_tokens: dict = {}


def get_auth_url() -> str:
    params = {
        "response_type": "code",
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "scope": settings.GOOGLE_HEALTH_SCOPES,
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{settings.GOOGLE_AUTH_URL}?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    """Exchange the OAuth authorization code for access + refresh tokens."""
    response = requests.post(
        settings.GOOGLE_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
        },
    )
    response.raise_for_status()
    tokens = response.json()
    _google_tokens["access_token"] = tokens["access_token"]
    _google_tokens["refresh_token"] = tokens.get("refresh_token")
    return tokens


def refresh_access_token() -> str:
    """Use the refresh token to get a new access token."""
    response = requests.post(
        settings.GOOGLE_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": _google_tokens.get("refresh_token", ""),
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
        },
    )
    response.raise_for_status()
    tokens = response.json()
    _google_tokens["access_token"] = tokens["access_token"]
    return tokens["access_token"]


def _get_headers() -> dict:
    """Build authorization headers for Google Health API requests."""
    return {"Authorization": f"Bearer {_google_tokens.get('access_token', '')}"}


def _build_date_range(target_date: date) -> dict:
    """Build the date range request body for a single day."""
    return {
        "range": {
            "start": {
                "date": {"year": target_date.year, "month": target_date.month, "day": target_date.day},
                "time": {"hours": 0, "minutes": 0, "seconds": 0, "nanos": 0},
            },
            "end": {
                "date": {"year": target_date.year, "month": target_date.month, "day": target_date.day},
                "time": {"hours": 23, "minutes": 59, "seconds": 59, "nanos": 0},
            },
        },
        "windowSizeDays": 1,
    }


# Maps data type to its filter field name for the list endpoint.
# Daily summary types use {type}.date, session types use {type}.interval fields.
DATA_TYPE_FILTERS = {
    "daily-resting-heart-rate": ("daily_resting_heart_rate", "date", "date"),
    "daily-respiratory-rate": ("daily_respiratory_rate", "date", "date"),
    "sleep": ("sleep", "interval.end_time", "timestamp"),
    "exercise": ("exercise", "interval.civil_start_time", "date"),
}


def _fetch_data(data_type: str, target_date: date, action: str = "list") -> dict:
    """Fetch health data for a given data type and date."""
    base = f"{settings.GOOGLE_HEALTH_API_BASE}/v4/users/me/dataTypes/{data_type}/dataPoints"

    if action == "dailyRollUp":
        url = f"{base}:dailyRollUp"
        body = _build_date_range(target_date)
        response = requests.post(url, json=body, headers=_get_headers())
    else:
        filter_name, filter_field, format_type = DATA_TYPE_FILTERS[data_type]
        if format_type == "timestamp":
            start = f"{target_date.isoformat()}T00:00:00Z"
            end = f"{(target_date + timedelta(days=1)).isoformat()}T00:00:00Z"
        else:
            start = target_date.isoformat()
            end = (target_date + timedelta(days=1)).isoformat()
        filter_expr = f'{filter_name}.{filter_field} >= "{start}" AND {filter_name}.{filter_field} < "{end}"'
        response = requests.get(base, params={"filter": filter_expr}, headers=_get_headers())

    if not response.ok:
        print(f"Google Health API error ({response.status_code}): {response.text}")
    response.raise_for_status()
    return response.json()


def fetch_resting_heart_rate(target_date: date) -> dict:
    """Fetch daily resting heart rate. Only supports list, not dailyRollUp."""
    return _fetch_data("daily-resting-heart-rate", target_date, action="list")


def fetch_sleep(target_date: date) -> dict:
    """Fetch sleep session data for a specific day."""
    return _fetch_data("sleep", target_date, action="list")


def fetch_breathing_rate(target_date: date) -> dict:
    """Fetch daily respiratory rate."""
    return _fetch_data("daily-respiratory-rate", target_date, action="list")


def fetch_exercise(target_date: date) -> dict:
    """Fetch exercise/activity data for a specific day."""
    return _fetch_data("exercise", target_date, action="list")


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
