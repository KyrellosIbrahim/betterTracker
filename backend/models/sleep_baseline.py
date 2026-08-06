# ORM model for personalized sleep score anchors.
# One row (provider-agnostic, id=1) holding the low/high anchor for each
# sub-metric, derived from the user's own sleep history by
# calibrate_sleep_baseline.py. The scoring service falls back to population
# defaults when no row exists.

from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime
from database import Base


class SleepBaseline(Base):
    __tablename__ = "sleep_baseline"

    id = Column(Integer, primary_key=True, index=True)
    duration_low = Column(Float, nullable=False)
    duration_high = Column(Float, nullable=False)
    deep_pct_low = Column(Float, nullable=False)
    deep_pct_high = Column(Float, nullable=False)
    rem_pct_low = Column(Float, nullable=False)
    rem_pct_high = Column(Float, nullable=False)
    awake_low = Column(Float, nullable=False)
    awake_high = Column(Float, nullable=False)
    sample_days = Column(Integer, nullable=False)
    computed_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
