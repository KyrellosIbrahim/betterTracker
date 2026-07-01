# ORM model for daily health data pulled from the Fitbit API.
# One row per day. Linked to game sessions by date for correlation analysis.

from sqlalchemy import Column, Integer, Float, Date
from database import Base


class HealthSnapshot(Base):
    __tablename__ = "health_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    resting_heart_rate = Column(Integer, nullable=True)
    avg_heart_rate = Column(Integer, nullable=True)
    sleep_score = Column(Integer, nullable=True)
    sleep_duration_minutes = Column(Float, nullable=True)
    breathing_rate = Column(Float, nullable=True)
    active_minutes = Column(Integer, nullable=True)
    exercise_count = Column(Integer, nullable=True)
    exercise_calories = Column(Integer, nullable=True)
