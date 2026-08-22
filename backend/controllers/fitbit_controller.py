# Routes for Google Health API data and OAuth authentication.
# Handles the Google OAuth login redirect, token callback, and health data endpoints.

import logging

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import date, timedelta
from database import get_db
from models.health_snapshot import HealthSnapshot
from services import fitbit_service, sleep_score_service
from schemas.fitbit import (
    HeartRateResponse,
    SleepResponse,
    BreathingRateResponse,
    HealthSnapshotResponse,
    TokenStatusResponse,
)

logger = logging.getLogger(__name__)

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


@router.get("/auth/status", response_model=TokenStatusResponse)
def get_token_status(db: Session = Depends(get_db)):
    """Report whether Google Health is connected, and why not if it isn't."""
    return fitbit_service.fetch_token_status(db)


@router.delete("/auth/token")
def delete_token(db: Session = Depends(get_db)):
    """Forget the stored Google token, e.g. to reconnect with a different account."""
    fitbit_service.disconnect(db)
    return {"message": "Token deleted successfully"}

# --- Health Data Endpoints ---
#
# Every target_date defaults to None rather than date.today(). A default
# argument is evaluated once at import, so date.today() would freeze "today"
# at whatever day the server started — a long-running process would quietly
# keep serving a stale date.


@router.get("/health/heartrate", response_model=HeartRateResponse)
def get_heart_rate(target_date: date | None = Query(default=None)):
    """Fetch resting heart rate for a given day. Defaults to today."""
    target_date = target_date or date.today()
    data = fitbit_service.fetch_resting_heart_rate(target_date)
    rhr = data["dataPoints"][0]["dailyRestingHeartRate"]["beatsPerMinute"] if data["dataPoints"] else None
    return HeartRateResponse(date=target_date, resting_heart_rate=rhr)


@router.get("/health/sleep", response_model=SleepResponse)
def get_sleep(target_date: date | None = Query(default=None)):
    """Fetch sleep data for a given day. Defaults to today."""
    target_date = target_date or date.today()
    data = fitbit_service.fetch_sleep(target_date)
    result = sleep_score_service.calculate_sleep_score(data)
    if result is None:
        return SleepResponse(date=target_date)

    metrics = result["metrics"]
    return SleepResponse(
        date=target_date,
        sleep_start=metrics.get("sleep_start"),
        sleep_end=metrics.get("sleep_end"),
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
def get_breathing_rate(target_date: date | None = Query(default=None)):
    """Fetch breathing rate for a given day. Defaults to today."""
    target_date = target_date or date.today()
    data = fitbit_service.fetch_breathing_rate(target_date)
    br = data["dataPoints"][0]["dailyRespiratoryRate"]["breathsPerMinute"] if data["dataPoints"] else None
    logger.debug("Breathing rate for %s: %s", target_date, br)
    return BreathingRateResponse(date=target_date, breathing_rate=br)


@router.get("/health/snapshot", response_model=HealthSnapshotResponse)
def get_health_snapshot(
    target_date: date | None = Query(default=None),
    force: bool = Query(default=False, description="Refetch even if the stored row is still fresh"),
    db: Session = Depends(get_db),
):
    """
    A day's health data, refetched from Google only when the stored row is
    older than SNAPSHOT_MAX_AGE_MINUTES. Cheap to call on every page load.
    """
    target_date = target_date or date.today()
    snapshot = fitbit_service.get_or_refresh_snapshot(target_date, db, force=force)
    if snapshot is None:
        # No data upstream for this day yet (e.g. asked before that night's sleep)
        return HealthSnapshotResponse(date=target_date)
    return snapshot


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
