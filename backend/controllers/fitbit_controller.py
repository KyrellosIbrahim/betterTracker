# Routes for Google Health API data and OAuth authentication.
# Handles the Google OAuth login redirect, token callback, and health data endpoints.

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import date, timedelta
from database import get_db
from models.health_snapshot import HealthSnapshot
from services import fitbit_service, sleep_score_service
from schemas.fitbit import HeartRateResponse, SleepResponse, BreathingRateResponse, HealthSnapshotResponse

router = APIRouter(tags=["Health"])


# --- Google OAuth Flow ---

@router.get("/auth/google/login")
def google_login():
    """Redirect the user to Google's OAuth consent screen for Health API access."""
    return RedirectResponse(url=fitbit_service.get_auth_url())


@router.get("/auth/google/callback")
def google_callback(code: str):
    """Handle the OAuth callback from Google, exchange code for tokens."""
    fitbit_service.exchange_code_for_token(code)
    return RedirectResponse(url="http://localhost:5173")


# --- Health Data Endpoints ---

@router.get("/health/heartrate", response_model=HeartRateResponse)
def get_heart_rate(target_date: date = Query(default=date.today())):
    """Fetch resting heart rate for a given day. Defaults to today."""
    data = fitbit_service.fetch_resting_heart_rate(target_date)
    rhr = data["dataPoints"][0]["dailyRestingHeartRate"]["beatsPerMinute"] if data["dataPoints"] else None
    return HeartRateResponse(date=target_date, resting_heart_rate=rhr)


@router.get("/health/sleep", response_model=SleepResponse)
def get_sleep(target_date: date = Query(default=date.today())):
    """Fetch sleep data for a given day. Defaults to today."""
    data = fitbit_service.fetch_sleep(target_date)
    result = sleep_score_service.calculate_sleep_score(data)
    if result is None:
        return SleepResponse(date=target_date)

    metrics = result["metrics"]
    return SleepResponse(
        date=target_date,
        duration_minutes=metrics["minutes_asleep"],
        deep_minutes=metrics["deep_minutes"],
        light_minutes=metrics["light_minutes"],
        rem_minutes=metrics["rem_minutes"],
        awake_minutes=metrics["awake_minutes"],
        sleep_score=result["score"],
        rating=result["rating"],
        components=result["components"],
    )


@router.get("/health/breathing-rate", response_model=BreathingRateResponse)
def get_breathing_rate(target_date: date = Query(default=date.today())):
    """Fetch breathing rate for a given day. Defaults to today."""
    data = fitbit_service.fetch_breathing_rate(target_date)
    br = data["dataPoints"][0]["dailyRespiratoryRate"]["breathsPerMinute"] if data["dataPoints"] else None
    print(f"Breathing rate response: {data}")
    return BreathingRateResponse(date=target_date, breathing_rate=br)


@router.get("/health/snapshot", response_model=HealthSnapshotResponse)
def get_health_snapshot(target_date: date = Query(default=date.today()), db: Session = Depends(get_db)):
    """Fetch all health data for a day and persist it to the database."""
    hr_response = get_heart_rate(target_date)
    sleep_response = get_sleep(target_date)
    br_response = get_breathing_rate(target_date)

    snapshot_data = {
        "resting_heart_rate": hr_response.resting_heart_rate,
        "sleep_score": sleep_response.sleep_score,
        "sleep_duration_minutes": sleep_response.duration_minutes,
        "deep_minutes": sleep_response.deep_minutes,
        "light_minutes": sleep_response.light_minutes,
        "rem_minutes": sleep_response.rem_minutes,
        "awake_minutes": sleep_response.awake_minutes,
        "breathing_rate": br_response.breathing_rate,
    }
    fitbit_service.save_health_snapshot(target_date, snapshot_data, db)

    return HealthSnapshotResponse(date=target_date, **snapshot_data)


@router.get("/health/snapshots", response_model=list[HealthSnapshotResponse])
def list_health_snapshots(days: int = Query(default=30, le=365), db: Session = Depends(get_db)):
    """List stored daily snapshots for the last N days, oldest first. Used for trend charts."""
    cutoff = date.today() - timedelta(days=days)
    return (
        db.query(HealthSnapshot)
        .filter(HealthSnapshot.date >= cutoff)
        .order_by(HealthSnapshot.date)
        .all()
    )
