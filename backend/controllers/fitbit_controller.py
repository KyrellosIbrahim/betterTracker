# Routes for Fitbit API data and OAuth authentication.
# Handles the OAuth login redirect, token callback, and health data endpoints.

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import date
from database import get_db
from services import fitbit_service
from schemas.fitbit import HeartRateResponse, SleepResponse, BreathingRateResponse, HealthSnapshotResponse

router = APIRouter(tags=["Fitbit"])


# --- OAuth Flow ---

@router.get("/auth/fitbit/login")
def fitbit_login():
    """Redirect the user to Fitbit's OAuth consent screen."""
    return RedirectResponse(url=fitbit_service.get_auth_url())


@router.get("/auth/fitbit/callback")
def fitbit_callback(code: str):
    """Handle the OAuth callback from Fitbit, exchange code for tokens."""
    fitbit_service.exchange_code_for_token(code)
    return RedirectResponse(url="http://localhost:5173")


# --- Health Data Endpoints ---

@router.get("/fitbit/heartrate", response_model=HeartRateResponse)
def get_heart_rate(target_date: date = Query(default=date.today())):
    """Fetch heart rate data for a given day. Defaults to today."""
    data = fitbit_service.fetch_heart_rate(target_date)
    # TODO: parse the Fitbit response into HeartRateResponse fields
    return HeartRateResponse(date=target_date)


@router.get("/fitbit/sleep", response_model=SleepResponse)
def get_sleep(target_date: date = Query(default=date.today())):
    """Fetch sleep data for a given day. Defaults to today."""
    data = fitbit_service.fetch_sleep(target_date)
    # TODO: parse the Fitbit response into SleepResponse fields
    return SleepResponse(date=target_date)


@router.get("/fitbit/breathing-rate", response_model=BreathingRateResponse)
def get_breathing_rate(target_date: date = Query(default=date.today())):
    """Fetch breathing rate for a given day. Defaults to today."""
    data = fitbit_service.fetch_breathing_rate(target_date)
    # TODO: parse the Fitbit response into BreathingRateResponse fields
    return BreathingRateResponse(date=target_date)


@router.get("/fitbit/snapshot", response_model=HealthSnapshotResponse)
def get_health_snapshot(target_date: date = Query(default=date.today()), db: Session = Depends(get_db)):
    """Fetch all health data for a day and persist it to the database."""
    # TODO: aggregate all Fitbit data, save via fitbit_service.save_health_snapshot
    return HealthSnapshotResponse(date=target_date)
