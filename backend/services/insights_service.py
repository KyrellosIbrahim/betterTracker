# Business logic for correlating Steam session data with Google Health data.
#
# Two alignment rules make these numbers mean what they claim to:
#
# 1. Gaming day — a session is attributed to the evening it belongs to, not the
#    calendar day it started in. Play at 1am is the previous night's gaming, so
#    the day boundary is GAMING_DAY_START_HOUR (4am by default), not midnight.
#
# 2. Recovery day — the sleep a gaming session affects is *the next morning's*.
#    A health snapshot dated D holds the sleep that ended on the morning of D
#    (sleep sessions are filtered by interval.end_time), so gaming day D is
#    joined to snapshot D+1. Resting heart rate follows the same rule: the
#    daily value is derived largely from overnight data.
#
# Metrics are averaged over distinct recovery days, not over sessions, so three
# sessions in one evening don't count that night's sleep three times.

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from config import settings
from models.game_session import GameSession
from models.health_snapshot import HealthSnapshot


def gaming_day(start_time: datetime) -> date:
    """The logical gaming day a session belongs to (see rule 1 above)."""
    return (start_time - timedelta(hours=settings.GAMING_DAY_START_HOUR)).date()


def recovery_date(day: date) -> date:
    """The snapshot date holding the sleep that followed a gaming day (rule 2)."""
    return day + timedelta(days=1)


def _average(values: list) -> float | None:
    present = [v for v in values if v is not None]
    return round(sum(present) / len(present), 1) if present else None


def _load(db: Session) -> tuple[list[GameSession], dict[date, HealthSnapshot]]:
    sessions = db.query(GameSession).all()
    snapshots = {snap.date: snap for snap in db.query(HealthSnapshot).all()}
    return sessions, snapshots


def _summarize(sessions: list[GameSession], snaps: list[HealthSnapshot]) -> dict:
    """Build the shared metric block for a group of sessions and their recovery days."""
    durations = [s.duration_minutes for s in sessions if s.duration_minutes is not None]
    return {
        "session_count": len(sessions),
        "recovery_days": len(snaps),
        "avg_session_minutes": _average(durations),
        "avg_resting_hr": _average([s.resting_heart_rate for s in snaps]),
        "avg_sleep_score": _average([s.sleep_score for s in snaps]),
        "avg_sleep_duration_minutes": _average([s.sleep_duration_minutes for s in snaps]),
        "avg_breathing_rate": _average([s.breathing_rate for s in snaps]),
    }


def _group_by(db: Session, key_of) -> dict:
    """
    Group sessions by key_of(session), collecting each group's sessions and the
    distinct next-morning snapshots that followed them. Sessions whose key is
    None (e.g. an untagged genre) are skipped.
    """
    sessions, snapshots = _load(db)
    groups: dict = {}

    for session in sessions:
        key = key_of(session)
        if key is None:
            continue
        group = groups.setdefault(key, {"sessions": [], "days": {}})
        group["sessions"].append(session)

        snapshot = snapshots.get(recovery_date(gaming_day(session.start_time)))
        if snapshot is not None:
            group["days"][snapshot.date] = snapshot

    return groups


def get_health_by_genre(db: Session) -> list[dict]:
    """
    Average next-morning health metrics for each game genre.
    Answers: "how do I recover after playing each genre?"
    """
    groups = _group_by(db, lambda s: s.genre)
    return [
        {"genre": genre, **_summarize(group["sessions"], list(group["days"].values()))}
        for genre, group in sorted(groups.items())
    ]


def get_health_by_competitive(db: Session) -> list[dict]:
    """
    Average next-morning health metrics for competitive vs non-competitive play.
    The core thesis of the project: does competitive gaming hurt recovery?
    """
    groups = _group_by(db, lambda s: bool(s.is_competitive))
    return [
        {"is_competitive": flag, **_summarize(group["sessions"], list(group["days"].values()))}
        for flag, group in sorted(groups.items())
    ]


def get_sleep_impact_by_genre(db: Session) -> list[dict]:
    """Next-morning sleep score after each genre, best first."""
    groups = _group_by(db, lambda s: s.genre)
    rows = [
        {
            "genre": genre,
            "avg_sleep_score": _average([s.sleep_score for s in group["days"].values()]),
            "sample_days": len(group["days"]),
        }
        for genre, group in groups.items()
    ]
    return sorted(rows, key=lambda r: (r["avg_sleep_score"] is None, -(r["avg_sleep_score"] or 0)))


def get_sleep_impact_by_competitive(db: Session) -> dict:
    """
    Compare next-morning sleep across three kinds of night: nights with at least
    one competitive session, nights with only casual sessions, and nights with
    no gaming at all.
    """
    sessions, snapshots = _load(db)

    # Classify each gaming day by whether any session that evening was competitive
    played: dict[date, bool] = {}
    for session in sessions:
        day = gaming_day(session.start_time)
        played[day] = played.get(day, False) or bool(session.is_competitive)

    buckets: dict[str, list[HealthSnapshot]] = {
        "competitive_days": [],
        "casual_only_days": [],
        "no_gaming_days": [],
    }
    for snapshot in snapshots.values():
        # The gaming day whose sleep this snapshot represents
        day = snapshot.date - timedelta(days=1)
        if day not in played:
            buckets["no_gaming_days"].append(snapshot)
        elif played[day]:
            buckets["competitive_days"].append(snapshot)
        else:
            buckets["casual_only_days"].append(snapshot)

    return {
        name: {
            "avg_sleep_score": _average([s.sleep_score for s in snaps]),
            "avg_sleep_duration_minutes": _average([s.sleep_duration_minutes for s in snaps]),
            "avg_resting_hr": _average([s.resting_heart_rate for s in snaps]),
            "sample_days": len(snaps),
        }
        for name, snaps in buckets.items()
    }
