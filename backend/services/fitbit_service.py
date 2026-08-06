# Business logic for Google Health API interactions (formerly Fitbit).
# Handles the Google OAuth 2.0 authorization flow and fetching health data
# (heart rate, sleep, breathing rate, exercise logs) via the Health API v4.

import requests
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from urllib.parse import urlencode
from config import settings
from database import SessionLocal
from models.health_snapshot import HealthSnapshot
from models.oauth_token import OAuthToken
from services import sleep_score_service

# In-memory cache of the Google tokens, backed by the oauth_tokens table
# so they survive server restarts.
_google_tokens: dict = {}


def _load_tokens() -> None:
    """Populate the in-memory token cache from the DB if it's empty."""
    if _google_tokens.get("access_token"):
        return
    db = SessionLocal()
    try:
        row = db.query(OAuthToken).filter(OAuthToken.provider == "google").first()
        if row:
            _google_tokens["access_token"] = row.access_token
            _google_tokens["refresh_token"] = row.refresh_token
    finally:
        db.close()


def _save_tokens() -> None:
    """Persist the current tokens to the DB, keeping the existing refresh token if none was issued."""
    db = SessionLocal()
    try:
        row = db.query(OAuthToken).filter(OAuthToken.provider == "google").first()
        if row:
            row.access_token = _google_tokens.get("access_token", "")
            if _google_tokens.get("refresh_token"):
                row.refresh_token = _google_tokens["refresh_token"]
        else:
            db.add(OAuthToken(
                provider="google",
                access_token=_google_tokens.get("access_token", ""),
                refresh_token=_google_tokens.get("refresh_token"),
            ))
        db.commit()
    finally:
        db.close()


def _record_auth_error(reason: str, needs_reauth: bool = False) -> None:
    """
    Record why an auth call failed. needs_reauth=True means only a fresh consent
    can fix it; other errors (e.g. bad client credentials) are recorded for
    debugging but don't ask the user to reconnect, because that wouldn't help.
    """
    db = SessionLocal()
    try:
        row = db.query(OAuthToken).filter(OAuthToken.provider == "google").first()
        if row:
            row.last_error = reason
            if needs_reauth:
                row.needs_reauth = True
            db.commit()
    finally:
        db.close()


def _clear_reauth():
    db = SessionLocal()
    try:
        row = db.query(OAuthToken).filter(OAuthToken.provider == "google").first()
        if row:
            row.needs_reauth = False
            row.last_error = None
            row.last_success_at = datetime.now()
            db.commit()
    finally:
        db.close()


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
    _save_tokens()
    _clear_reauth()
    return tokens


def refresh_access_token() -> str:
    """Use the refresh token to get a new access token."""
    _load_tokens()
    response = requests.post(
        settings.GOOGLE_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": _google_tokens.get("refresh_token", ""),
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
        },
    )
    # A transport-level failure (timeout, DNS, connection refused) never reaches
    # here — requests raises — so a network blip can't be mistaken for a dead grant.
    if response.status_code in (400, 401):
        try:
            error = response.json().get("error") or "unknown_error"
        except ValueError:
            error = f"non-JSON response: {response.text[:120]}"
        # invalid_grant is Google's definitive "this refresh token is dead"
        _record_auth_error(
            f"{error}: refresh failed with HTTP {response.status_code}",
            needs_reauth=(error == "invalid_grant"),
        )
    response.raise_for_status()
    tokens = response.json()
    _google_tokens["access_token"] = tokens["access_token"]
    _save_tokens()
    return tokens["access_token"]


def _get_headers() -> dict:
    """Build authorization headers for Google Health API requests."""
    _load_tokens()
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
    """Fetch health data for a given data type and date. Refreshes the access token on 401."""
    base = f"{settings.GOOGLE_HEALTH_API_BASE}/v4/users/me/dataTypes/{data_type}/dataPoints"

    def make_request():
        if action == "dailyRollUp":
            url = f"{base}:dailyRollUp"
            body = _build_date_range(target_date)
            return requests.post(url, json=body, headers=_get_headers())
        filter_name, filter_field, format_type = DATA_TYPE_FILTERS[data_type]
        if format_type == "timestamp":
            start = f"{target_date.isoformat()}T00:00:00Z"
            end = f"{(target_date + timedelta(days=1)).isoformat()}T00:00:00Z"
        else:
            start = target_date.isoformat()
            end = (target_date + timedelta(days=1)).isoformat()
        filter_expr = f'{filter_name}.{filter_field} >= "{start}" AND {filter_name}.{filter_field} < "{end}"'
        return requests.get(base, params={"filter": filter_expr}, headers=_get_headers())

    response = make_request()
    if response.status_code == 401:
        # Access token expired (e.g. after a server restart) — refresh and retry once
        refresh_access_token()
        response = make_request()

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


def build_snapshot_data(target_date: date) -> dict:
    """
    Fetch every health metric for a day and map it to HealthSnapshot column values.
    Shared by the /health/snapshot endpoint and the backfill script so the two
    can't drift apart. Values are None where the API had no data for that day.
    """
    hr_data = fetch_resting_heart_rate(target_date)
    hr_points = hr_data.get("dataPoints") or []
    resting_hr = hr_points[0]["dailyRestingHeartRate"]["beatsPerMinute"] if hr_points else None

    br_data = fetch_breathing_rate(target_date)
    br_points = br_data.get("dataPoints") or []
    breathing_rate = br_points[0]["dailyRespiratoryRate"]["breathsPerMinute"] if br_points else None

    sleep = sleep_score_service.calculate_sleep_score(fetch_sleep(target_date)) or {}
    metrics = sleep.get("metrics", {})

    return {
        "resting_heart_rate": int(resting_hr) if resting_hr is not None else None,
        "sleep_score": sleep.get("score"),
        "sleep_duration_minutes": metrics.get("minutes_asleep"),
        "deep_minutes": metrics.get("deep_minutes"),
        "light_minutes": metrics.get("light_minutes"),
        "rem_minutes": metrics.get("rem_minutes"),
        "awake_minutes": metrics.get("awake_minutes"),
        "breathing_rate": float(breathing_rate) if breathing_rate is not None else None,
    }


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


def fetch_token_status(db: Session) -> dict:
    """
    Report the stored Google token's state without calling Google.
    `connected` means "we hold a refresh token Google hasn't rejected" — the
    access token is a ~1h credential that _fetch_data renews automatically, so
    it says nothing about whether the connection is alive.
    """
    row = db.query(OAuthToken).filter(OAuthToken.provider == "google").first()
    return dict(
        connected=bool(row and row.refresh_token and not row.needs_reauth),
        has_refresh_token=bool(row and row.refresh_token),
        needs_reauth=bool(row and row.needs_reauth),
        last_error=row.last_error if row else None,
        last_success_at=row.last_success_at if row else None,
        updated_at=row.updated_at if row else None,
    )


def record_sync_success(db: Session) -> None:
    """Stamp the last time we successfully pulled health data."""
    row = db.query(OAuthToken).filter(OAuthToken.provider == "google").first()
    if row:
        row.last_success_at = datetime.now()
        db.commit()


def disconnect(db: Session) -> None:
    """
    Forget the stored Google token. Clearing the in-memory cache is the part
    that's easy to miss — without it the process keeps using the deleted token
    until it restarts.
    """
    db.query(OAuthToken).filter(OAuthToken.provider == "google").delete()
    db.commit()
    _google_tokens.clear()
    
