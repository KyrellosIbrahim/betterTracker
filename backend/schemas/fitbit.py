# Pydantic schemas for Google Health API response validation.
# These define the shape of health data returned from health-related endpoints.

from pydantic import BaseModel
from typing import Optional
from datetime import date


class HeartRateResponse(BaseModel):
    """Resting heart rate data for a given day (from daily-resting-heart-rate)."""
    date: date
    resting_heart_rate: Optional[int] = None


class SleepScoreComponents(BaseModel):
    """Per-component breakdown of the sleep score (duration 50 / quality 25 / restoration 25)."""
    duration: float
    quality: float
    restoration: float


class SleepResponse(BaseModel):
    """Sleep data for a given day (from sleep data type)."""
    date: date
    duration_minutes: Optional[float] = None
    deep_minutes: Optional[int] = None
    light_minutes: Optional[int] = None
    rem_minutes: Optional[int] = None
    awake_minutes: Optional[int] = None
    sleep_score: Optional[int] = None
    rating: Optional[str] = None
    components: Optional[SleepScoreComponents] = None


class BreathingRateResponse(BaseModel):
    """Breathing rate data for a given day (from dailyRespiratoryRate)."""
    date: date
    breathing_rate: Optional[float] = None


class HealthSnapshotResponse(BaseModel):
    """Combined health data for a single day."""
    model_config = {"from_attributes": True}

    date: date
    resting_heart_rate: Optional[int] = None
    sleep_score: Optional[int] = None
    sleep_duration_minutes: Optional[float] = None
    deep_minutes: Optional[int] = None
    light_minutes: Optional[int] = None
    rem_minutes: Optional[int] = None
    awake_minutes: Optional[int] = None
    breathing_rate: Optional[float] = None
