# Tests for the Games-overhaul insights: enriched bucket metrics, playtime
# buckets, the physical-activity interaction, and the competitive-tag backfill.
# Same alignment rules as test_insights.py (gaming day 4am–4am, recovery = next
# morning).

from datetime import date, datetime, timedelta

from models.game_session import GameSession
from models.health_snapshot import HealthSnapshot
from services import insights_service as ins
from services import steam_service


def add_snapshot(db, day, *, score=80, rhr=60, deep=90, rem=100, breathing=15.0,
                 spo2=97.0, active=None, steps=None):
    snap = HealthSnapshot(
        date=day, sleep_score=score, resting_heart_rate=rhr,
        sleep_duration_minutes=420.0, deep_minutes=deep, rem_minutes=rem,
        breathing_rate=breathing, spo2=spo2, active_minutes=active, steps=steps,
    )
    db.add(snap)
    db.commit()
    return snap


def add_session(db, start, end, *, competitive=False, genre="Action", name="Game", game_id=1):
    session = GameSession(
        game_id=game_id, game_name=name, genre=genre, is_competitive=competitive,
        start_time=start, end_time=end,
        duration_minutes=(end - start).total_seconds() / 60 if end else None,
    )
    db.add(session)
    db.commit()
    return session


# --- Enriched bucket metrics ---

def test_bucket_stats_includes_new_metrics(db):
    add_snapshot(db, date(2026, 7, 15), score=60, deep=80, rem=110, breathing=16.0, spo2=95.5)
    add_session(db, datetime(2026, 7, 14, 20, 0), datetime(2026, 7, 14, 22, 0), competitive=True)

    bucket = ins.get_sleep_impact_by_competitive(db)["competitive_days"]
    assert bucket["avg_deep_minutes"] == 80.0
    assert bucket["avg_rem_minutes"] == 110.0
    assert bucket["avg_breathing_rate"] == 16.0
    assert bucket["avg_spo2"] == 95.5


# --- Playtime buckets ---

def test_playtime_buckets_by_total_daily_minutes(db):
    # (gaming day, total minutes, expected bucket)
    cases = [(14, 45, "under_1h"), (16, 120, "1_to_3h"), (18, 240, "over_3h")]
    for day, minutes, _ in cases:
        add_snapshot(db, date(2026, 7, day + 1), score=70)  # recovery morning
        start = datetime(2026, 7, day, 20, 0)
        add_session(db, start, start + timedelta(minutes=minutes))

    out = ins.get_playtime_impact(db)
    for _, minutes, bucket in cases:
        assert out[bucket]["sample_days"] == 1
        assert out[bucket]["avg_playtime_minutes"] == minutes


def test_playtime_sums_multiple_sessions_in_a_day(db):
    add_snapshot(db, date(2026, 7, 15), score=70)
    for hour in (18, 20, 22):  # 3 x 60min = 180 -> over_3h boundary
        add_session(db, datetime(2026, 7, 14, hour, 0), datetime(2026, 7, 14, hour + 1, 0))

    out = ins.get_playtime_impact(db)
    assert out["over_3h"]["sample_days"] == 1
    assert out["over_3h"]["avg_playtime_minutes"] == 180


# --- Activity interaction ---

def test_activity_interaction_splits_active_vs_sedentary(db):
    # Active gaming day: day 14 active=60, recovery 15
    add_snapshot(db, date(2026, 7, 14), active=60)
    add_snapshot(db, date(2026, 7, 15), score=60)
    add_session(db, datetime(2026, 7, 14, 20, 0), datetime(2026, 7, 14, 22, 0))
    # Sedentary gaming day: day 16 active=10, recovery 17
    add_snapshot(db, date(2026, 7, 16), active=10)
    add_snapshot(db, date(2026, 7, 17), score=70)
    add_session(db, datetime(2026, 7, 16, 20, 0), datetime(2026, 7, 16, 22, 0))

    out = ins.get_activity_interaction(db)
    assert out["gaming_active"]["sample_days"] == 1
    assert out["gaming_active"]["avg_sleep_score"] == 60.0
    assert out["gaming_sedentary"]["sample_days"] == 1
    assert out["gaming_sedentary"]["avg_sleep_score"] == 70.0


def test_activity_interaction_excludes_unknown_activity(db):
    # Gaming on day 25 but no snapshot for day 25 -> activity unknown -> excluded
    add_snapshot(db, date(2026, 7, 26), score=50)
    add_session(db, datetime(2026, 7, 25, 20, 0), datetime(2026, 7, 25, 22, 0))

    out = ins.get_activity_interaction(db)
    assert out["gaming_active"]["sample_days"] == 0
    assert out["gaming_sedentary"]["sample_days"] == 0


# --- Weekly playtime vs sleep ---

def test_weekly_playtime_vs_sleep_groups_by_week(db):
    # Two gaming days in the same ISO week (Mon 2026-07-13 .. Sun 07-19)
    add_snapshot(db, date(2026, 7, 15), score=60)
    add_snapshot(db, date(2026, 7, 17), score=80)
    add_session(db, datetime(2026, 7, 14, 20, 0), datetime(2026, 7, 14, 21, 0))  # 60m
    add_session(db, datetime(2026, 7, 16, 20, 0), datetime(2026, 7, 16, 21, 30))  # 90m

    rows = ins.get_weekly_playtime_vs_sleep(db)
    assert len(rows) == 1
    assert rows[0]["week_start"] == "2026-07-13"
    assert rows[0]["total_minutes"] == 150
    assert rows[0]["avg_sleep_score"] == 70.0  # (60 + 80) / 2


# --- Competitive tag backfill ---

def test_tagging_competitive_backfills_existing_sessions(db):
    add_snapshot(db, date(2026, 7, 15), score=60)
    add_session(db, datetime(2026, 7, 14, 20, 0), datetime(2026, 7, 14, 22, 0),
                competitive=False, game_id=42, name="Ranked Thing")

    # Before tagging: the night reads as casual-only.
    before = ins.get_sleep_impact_by_competitive(db)
    assert before["casual_only_days"]["sample_days"] == 1
    assert before["competitive_days"]["sample_days"] == 0

    steam_service.upsert_game(app_id=42, game_name="Ranked Thing", genre="Action",
                              is_competitive=True, db=db)

    # The existing session was rewritten, so it now reads as competitive.
    session = db.query(GameSession).filter(GameSession.game_id == 42).one()
    assert session.is_competitive is True

    after = ins.get_sleep_impact_by_competitive(db)
    assert after["competitive_days"]["sample_days"] == 1
    assert after["casual_only_days"]["sample_days"] == 0
