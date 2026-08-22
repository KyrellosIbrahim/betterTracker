# Tests for the session <-> health alignment rules.
#
# These encode the two decisions everything else depends on:
#   1. a gaming day runs 4am -> 4am, so a 1am session belongs to the night before
#   2. the sleep a session affects is the NEXT morning's snapshot

from datetime import date, datetime, timedelta

import pytest

from models.game_session import GameSession
from models.health_snapshot import HealthSnapshot
from services import insights_service as ins


def add_snapshot(db, day, *, score=80, rhr=60, bed_hour=23):
    snap = HealthSnapshot(
        date=day,
        sleep_score=score,
        resting_heart_rate=rhr,
        sleep_duration_minutes=420.0,
        # Bedtime belongs to the previous evening — this row is that sleep's morning.
        sleep_start=datetime.combine(day - timedelta(days=1), datetime.min.time()).replace(hour=bed_hour),
        sleep_end=datetime.combine(day, datetime.min.time()).replace(hour=7),
    )
    db.add(snap)
    db.commit()
    return snap


def add_session(db, start, end, *, competitive=False, genre="Action", name="Game"):
    session = GameSession(
        game_id=1, game_name=name, genre=genre, is_competitive=competitive,
        start_time=start, end_time=end,
        duration_minutes=(end - start).total_seconds() / 60 if end else None,
    )
    db.add(session)
    db.commit()
    return session


# --- Gaming day boundary ---

@pytest.mark.parametrize(
    "moment,expected",
    [
        (datetime(2026, 7, 14, 23, 0), date(2026, 7, 14)),   # 11pm Tue -> Tue
        (datetime(2026, 7, 15, 1, 30), date(2026, 7, 14)),   # 1:30am Wed -> still Tue night
        (datetime(2026, 7, 15, 3, 59), date(2026, 7, 14)),   # just before the boundary
        (datetime(2026, 7, 15, 4, 0), date(2026, 7, 15)),    # boundary itself
        (datetime(2026, 7, 15, 12, 0), date(2026, 7, 15)),   # midday
    ],
)
def test_gaming_day_boundary(moment, expected):
    assert ins.gaming_day(moment) == expected


def test_recovery_date_is_the_next_morning():
    assert ins.recovery_date(date(2026, 7, 14)) == date(2026, 7, 15)


# --- Next-morning join ---

def test_session_joins_to_next_mornings_sleep(db):
    add_snapshot(db, date(2026, 7, 15), score=70)   # the morning after
    add_snapshot(db, date(2026, 7, 14), score=95)   # same-day; must NOT be used
    add_session(db, datetime(2026, 7, 14, 20, 0), datetime(2026, 7, 14, 22, 0), competitive=True)

    row = next(r for r in ins.get_health_by_competitive(db) if r["is_competitive"])
    assert row["avg_sleep_score"] == 70.0, "must use the next morning, not the same day"


def test_post_midnight_session_counts_as_previous_evening(db):
    add_snapshot(db, date(2026, 7, 15), score=70)
    add_session(db, datetime(2026, 7, 15, 1, 0), datetime(2026, 7, 15, 3, 0), competitive=True)

    row = next(r for r in ins.get_health_by_competitive(db) if r["is_competitive"])
    assert row["recovery_days"] == 1
    assert row["avg_sleep_score"] == 70.0


def test_metrics_average_over_days_not_sessions(db):
    """Three sessions in one evening must not count that night's sleep three times."""
    add_snapshot(db, date(2026, 7, 15), score=70)
    for hour in (18, 20, 22):
        add_session(db, datetime(2026, 7, 14, hour, 0), datetime(2026, 7, 14, hour + 1, 0), competitive=True)

    row = next(r for r in ins.get_health_by_competitive(db) if r["is_competitive"])
    assert row["session_count"] == 3
    assert row["recovery_days"] == 1


def test_spread_reported_alongside_mean(db):
    for day, score in [(15, 60), (17, 90)]:
        add_snapshot(db, date(2026, 7, day), score=score)
        add_session(db, datetime(2026, 7, day - 1, 20, 0), datetime(2026, 7, day - 1, 22, 0), competitive=True)

    row = next(r for r in ins.get_health_by_competitive(db) if r["is_competitive"])
    assert row["sleep_score_min"] == 60 and row["sleep_score_max"] == 90


# --- Three-bucket sleep impact ---

def test_competitive_casual_and_no_gaming_buckets(db):
    add_snapshot(db, date(2026, 7, 15), score=60)   # after competitive
    add_snapshot(db, date(2026, 7, 17), score=70)   # after casual
    add_snapshot(db, date(2026, 7, 20), score=90)   # no gaming
    add_session(db, datetime(2026, 7, 14, 20, 0), datetime(2026, 7, 14, 22, 0), competitive=True)
    add_session(db, datetime(2026, 7, 16, 20, 0), datetime(2026, 7, 16, 22, 0), competitive=False)

    out = ins.get_sleep_impact_by_competitive(db)
    assert out["competitive_days"]["avg_sleep_score"] == 60.0
    assert out["casual_only_days"]["avg_sleep_score"] == 70.0
    assert out["no_gaming_days"]["avg_sleep_score"] == 90.0


def test_any_competitive_session_makes_the_night_competitive(db):
    add_snapshot(db, date(2026, 7, 15), score=60)
    add_session(db, datetime(2026, 7, 14, 18, 0), datetime(2026, 7, 14, 19, 0), competitive=False)
    add_session(db, datetime(2026, 7, 14, 20, 0), datetime(2026, 7, 14, 21, 0), competitive=True)

    out = ins.get_sleep_impact_by_competitive(db)
    assert out["competitive_days"]["sample_days"] == 1
    assert out["casual_only_days"]["sample_days"] == 0


# --- Wind-down ---

def test_wind_down_buckets_by_gap_to_bedtime(db):
    # bedtime is 23:00 the evening before each snapshot date
    cases = [(15, 10, "under_30min"), (17, 60, "30_to_90min"), (19, 180, "over_90min")]
    for day, gap_minutes, _ in cases:
        add_snapshot(db, date(2026, 7, day))
        bedtime = datetime(2026, 7, day - 1, 23, 0)
        end = bedtime - timedelta(minutes=gap_minutes)
        add_session(db, end - timedelta(hours=1), end)

    out = ins.get_wind_down_impact(db)
    for _, gap_minutes, bucket in cases:
        assert out[bucket]["sample_days"] == 1
        assert out[bucket]["avg_gap_minutes"] == pytest.approx(gap_minutes, abs=0.5)


def test_wind_down_ignores_negative_gap(db):
    """Session ended after bedtime — not a wind-down measurement."""
    add_snapshot(db, date(2026, 7, 15))          # bed 23:00 on the 14th
    add_session(db, datetime(2026, 7, 14, 23, 30), datetime(2026, 7, 15, 1, 0))

    out = ins.get_wind_down_impact(db)
    assert sum(b["sample_days"] for b in out.values()) == 0


def test_wind_down_ignores_outage_inflated_session(db):
    """
    A failed poll leaves a session open until polling recovers, so end_time is
    bogus. Since the gap is measured from end_time, those must be dropped.
    """
    add_snapshot(db, date(2026, 7, 15))
    add_session(db, datetime(2026, 7, 13, 20, 0), datetime(2026, 7, 14, 22, 0))  # 26h

    out = ins.get_wind_down_impact(db)
    assert sum(b["sample_days"] for b in out.values()) == 0


def test_open_session_is_skipped(db):
    add_snapshot(db, date(2026, 7, 15))
    add_session(db, datetime(2026, 7, 14, 20, 0), None)

    out = ins.get_wind_down_impact(db)
    assert sum(b["sample_days"] for b in out.values()) == 0


# --- Late night ---

def test_late_night_uses_gaming_day_not_clock_hour(db):
    """
    A session ending at 1am has hour == 1, which naively looks "early". It must
    be judged against 11pm on the *gaming* day.
    """
    add_snapshot(db, date(2026, 7, 15), score=60)
    add_session(db, datetime(2026, 7, 14, 23, 0), datetime(2026, 7, 15, 1, 0))

    out = ins.get_late_night_impact(db)
    assert out["late_night_gaming"]["sample_days"] == 1
    assert out["earlier_gaming"]["sample_days"] == 0


def test_early_evening_session_is_not_late_night(db):
    add_snapshot(db, date(2026, 7, 15), score=60)
    add_session(db, datetime(2026, 7, 14, 18, 0), datetime(2026, 7, 14, 20, 0))

    out = ins.get_late_night_impact(db)
    assert out["earlier_gaming"]["sample_days"] == 1
    assert out["late_night_gaming"]["sample_days"] == 0


def test_days_without_gaming_land_in_no_gaming(db):
    add_snapshot(db, date(2026, 7, 20), score=90)
    out = ins.get_late_night_impact(db)
    assert out["no_gaming"]["sample_days"] == 1


def test_empty_database_returns_zeroed_buckets(db):
    out = ins.get_sleep_impact_by_competitive(db)
    assert all(b["sample_days"] == 0 and b["avg_sleep_score"] is None for b in out.values())
    assert ins.get_health_by_competitive(db) == []
