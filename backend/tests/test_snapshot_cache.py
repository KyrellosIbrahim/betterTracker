# Tests for the /health/snapshot freshness rules.
#
# The Google call is stubbed throughout — these assert *when* we call out,
# never what the API returns.

from datetime import date, datetime, timedelta

import pytest

from models.health_snapshot import HealthSnapshot
from services import fitbit_service as fs


@pytest.fixture
def stub_google(monkeypatch):
    """Replace the network call and record how often it happens."""
    calls = []

    def fake(target_date):
        calls.append(target_date)
        return {
            "resting_heart_rate": 60, "sleep_score": 80, "sleep_duration_minutes": 420.0,
            "deep_minutes": 80, "light_minutes": 250, "rem_minutes": 90, "awake_minutes": 10,
            "breathing_rate": 15.0, "sleep_start": datetime(2026, 8, 4, 23, 0),
            "sleep_end": datetime(2026, 8, 5, 7, 0),
        }

    monkeypatch.setattr(fs, "build_snapshot_data", fake)
    return calls


def test_first_fetch_hits_google_and_stamps_synced_at(db, stub_google):
    snap = fs.get_or_refresh_snapshot(date.today(), db)
    assert len(stub_google) == 1
    assert snap.synced_at is not None


def test_fresh_row_is_served_from_cache(db, stub_google):
    fs.get_or_refresh_snapshot(date.today(), db)
    fs.get_or_refresh_snapshot(date.today(), db)
    assert len(stub_google) == 1, "a fresh row must not trigger a second call"


def test_stale_row_is_refetched(db, stub_google):
    fs.get_or_refresh_snapshot(date.today(), db)
    db.query(HealthSnapshot).update({"synced_at": datetime.now() - timedelta(minutes=90)})
    db.commit()
    fs.get_or_refresh_snapshot(date.today(), db)
    assert len(stub_google) == 2


def test_force_bypasses_the_ttl(db, stub_google):
    fs.get_or_refresh_snapshot(date.today(), db)
    fs.get_or_refresh_snapshot(date.today(), db, force=True)
    assert len(stub_google) == 2


def test_settled_past_day_is_never_refetched(db, stub_google):
    """
    Beyond the sync window a day is final. Rows written before synced_at existed
    have none, and without this rule they would refetch forever.
    """
    old = date.today() - timedelta(days=30)
    db.add(HealthSnapshot(date=old, sleep_score=88, synced_at=None))
    db.commit()

    snap = fs.get_or_refresh_snapshot(old, db)
    assert stub_google == [], "a settled day must not hit Google"
    assert snap.sleep_score == 88


def test_recent_day_inside_window_is_refetched_when_unstamped(db, stub_google):
    recent = date.today() - timedelta(days=1)
    db.add(HealthSnapshot(date=recent, sleep_score=88, synced_at=None))
    db.commit()

    fs.get_or_refresh_snapshot(recent, db)
    assert len(stub_google) == 1


def test_day_with_no_upstream_data_writes_no_row(db, monkeypatch):
    monkeypatch.setattr(fs, "build_snapshot_data", lambda d: {"sleep_score": None, "resting_heart_rate": None})
    assert fs.get_or_refresh_snapshot(date.today(), db) is None
    assert db.query(HealthSnapshot).count() == 0, "an all-empty day must not create a row"


def test_empty_response_keeps_existing_row(db, monkeypatch):
    """A transient empty response must not wipe data we already have."""
    today = date.today()
    db.add(HealthSnapshot(date=today, sleep_score=88, synced_at=datetime.now() - timedelta(hours=5)))
    db.commit()

    monkeypatch.setattr(fs, "build_snapshot_data", lambda d: {"sleep_score": None, "resting_heart_rate": None})
    snap = fs.get_or_refresh_snapshot(today, db)
    assert snap is not None and snap.sleep_score == 88


def test_save_updates_rather_than_duplicating(db, stub_google):
    fs.get_or_refresh_snapshot(date.today(), db)
    fs.get_or_refresh_snapshot(date.today(), db, force=True)
    assert db.query(HealthSnapshot).count() == 1
