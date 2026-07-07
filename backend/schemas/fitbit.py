# Pydantic schemas for Google Health API response validation.
# These define the shape of health data returned from health-related endpoints.

from pydantic import BaseModel
from typing import Optional
from datetime import date


class HeartRateResponse(BaseModel):
    """Resting heart rate data for a given day (from dailyRestingHeartRate)."""
    date: date
    resting_heart_rate: Optional[int] = None


class SleepResponse(BaseModel):
    """Sleep data for a given day (from sleep data type)."""
    date: date
    sleep_score: Optional[int] = None
    duration_minutes: Optional[float] = None


class BreathingRateResponse(BaseModel):
    """Breathing rate data for a given day (from dailyRespiratoryRate)."""
    date: date
    breathing_rate: Optional[float] = None


class HealthSnapshotResponse(BaseModel):
    """Combined health data for a single day."""
    date: date
    resting_heart_rate: Optional[int] = None
    sleep_score: Optional[int] = None
    sleep_duration_minutes: Optional[float] = None
    breathing_rate: Optional[float] = None
    active_minutes: Optional[int] = None
    exercise_count: Optional[int] = None
    exercise_calories: Optional[int] = None
