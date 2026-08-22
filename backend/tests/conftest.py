# Shared fixtures.
#
# Anything touching the DB uses a throwaway SQLite file built by the models,
# never bettertracker.db — tests must not be able to damage real health data.

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
import models  # noqa: F401  (registers every table on Base.metadata)


@pytest.fixture
def db(tmp_path):
    """A fresh, empty database per test."""
    engine = create_engine(f"sqlite:///{tmp_path}/test.db", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def anchors():
    """
    Fixed scoring anchors so score assertions don't depend on whatever personal
    baseline happens to be in the developer's database.
    """
    return {
        "duration_minutes": (360.0, 480.0),
        "deep_pct": (0.13, 0.23),
        "rem_pct": (0.15, 0.25),
        "awake_minutes": (5.0, 40.0),
    }


def sleep_response(
    *,
    minutes_asleep=450,
    deep=80,
    light=265,
    rem=105,
    awake=30,
    in_period=480,
    start="2026-08-05T04:07:00Z",
    end="2026-08-05T12:32:00Z",
    offset="-18000s",
    sleep_type="STAGES",
    nap=False,
):
    """
    Build a Google Health sleep payload. Numeric fields are strings on purpose:
    the real API serializes int64 that way, which has already caused one bug.
    """
    return {
        "dataPoints": [
            {
                "sleep": {
                    "type": sleep_type,
                    "metadata": {"nap": nap} if nap else {},
                    "interval": {
                        "startTime": start,
                        "startUtcOffset": offset,
                        "endTime": end,
                        "endUtcOffset": offset,
                    },
                    "summary": {
                        "minutesAsleep": str(minutes_asleep),
                        "minutesInSleepPeriod": str(in_period),
                        "minutesAwake": str(awake),
                        "minutesToFallAsleep": "0",
                        "stagesSummary": [
                            {"type": "DEEP", "minutes": str(deep)},
                            {"type": "LIGHT", "minutes": str(light)},
                            {"type": "REM", "minutes": str(rem)},
                            {"type": "AWAKE", "minutes": str(awake)},
                        ],
                    },
                }
            }
        ]
    }
