# ORM model for daily health data pulled from the Google Health API.
# One row per day. Linked to game sessions by date for correlation analysis.

from sqlalchemy import Column, Integer, Float, Date, DateTime
from database import Base


class HealthSnapshot(Base):
    __tablename__ = "health_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    resting_heart_rate = Column(Integer, nullable=True)
    sleep_start = Column(DateTime, nullable=True)
    sleep_end = Column(DateTime, nullable=True)
    sleep_score = Column(Integer, nullable=True)
    sleep_duration_minutes = Column(Float, nullable=True)
    deep_minutes = Column(Integer, nullable=True)
    light_minutes = Column(Integer, nullable=True)
    rem_minutes = Column(Integer, nullable=True)
    awake_minutes = Column(Integer, nullable=True)
    breathing_rate = Column(Float, nullable=True)
    # When this row was last pulled from Google. Staleness is per-day: today's
    # row goes stale hourly, a row from June never needs refetching again.
    synced_at = Column(DateTime, nullable=True)
