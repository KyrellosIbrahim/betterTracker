# Routes for Google Health API data and OAuth authentication.
# Handles the Google OAuth login redirect, token callback, and health data endpoints.

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import date
from database import get_db
from services import fitbit_service
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
    print(f"Heart rate response: {data}")
    return HeartRateResponse(date=target_date)


@router.get("/health/sleep", response_model=SleepResponse)
def get_sleep(target_date: date = Query(default=date.today())):
    """Fetch sleep data for a given day. Defaults to today."""
    data = fitbit_service.fetch_sleep(target_date)
    print(f"Sleep response: {data}")
    return SleepResponse(date=target_date)


@router.get("/health/breathing-rate", response_model=BreathingRateResponse)
def get_breathing_rate(target_date: date = Query(default=date.today())):
    """Fetch breathing rate for a given day. Defaults to today."""
    data = fitbit_service.fetch_breathing_rate(target_date)
    print(f"Breathing rate response: {data}")
    return BreathingRateResponse(date=target_date)


@router.get("/health/snapshot", response_model=HealthSnapshotResponse)
def get_health_snapshot(target_date: date = Query(default=date.today()), db: Session = Depends(get_db)):
    """Fetch all health data for a day and persist it to the database."""
    # TODO: aggregate all health data, save via fitbit_service.save_health_snapshot
    return HealthSnapshotResponse(date=target_date)
