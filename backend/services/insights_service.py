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

from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from config import settings
from models.game_session import GameSession
from models.health_snapshot import HealthSnapshot

# Sessions longer than this are almost certainly polling artifacts rather than
# real marathons: when the Steam poll fails (wifi drop, laptop sleep) the open
# session isn't closed until polling recovers, so end_time lands late. The
# wind-down gap is measured *from* end_time, so an inflated one would
# manufacture a fake-short gap — exactly the value we're trying to measure.
MAX_PLAUSIBLE_SESSION_MINUTES = 720

# A gap outside this range isn't measuring wind-down at all: negative means
# sleep began before gaming ended, and very large means you gamed in the
# morning rather than before bed.
MAX_WIND_DOWN_GAP_MINUTES = 720

# (name, low, high) in minutes — how long before bed the last session ended.
WIND_DOWN_BUCKETS = (
    ("under_30min", 0, 30),
    ("30_to_90min", 30, 90),
    ("over_90min", 90, MAX_WIND_DOWN_GAP_MINUTES + 1),
)

# (name, low, high) in minutes — a gaming day's total playtime. `high` on the
# last bucket is generous; a day's summed sessions won't exceed 24h anyway.
PLAYTIME_BUCKETS = (
    ("under_1h", 0, 60),
    ("1_to_3h", 60, 180),
    ("over_3h", 180, 24 * 60),
)


def gaming_day(start_time: datetime) -> date:
    """The logical gaming day a session belongs to (see rule 1 above)."""
    return (start_time - timedelta(hours=settings.GAMING_DAY_START_HOUR)).date()


def recovery_date(day: date) -> date:
    """The snapshot date holding the sleep that followed a gaming day (rule 2)."""
    return day + timedelta(days=1)


def _average(values: list) -> float | None:
    present = [v for v in values if v is not None]
    return round(sum(present) / len(present), 1) if present else None


def _spread(values: list) -> tuple[float | None, float | None]:
    """
    Min and max alongside the mean. Two averages that differ by a hair look like
    a finding until you see their ranges overlap completely — this is what keeps
    a comparison card honest once both sides clear the sample-size floor.
    """
    present = [v for v in values if v is not None]
    return (min(present), max(present)) if present else (None, None)


def _bucket_stats(snaps: list[HealthSnapshot]) -> dict:
    """
    Shared metric block for a bucket of recovery mornings. Every bucket-based
    insight returns this same set, so the frontend can switch which metric it
    charts without needing a different endpoint per metric.
    """
    scores = [s.sleep_score for s in snaps]
    score_min, score_max = _spread(scores)
    return {
        "avg_sleep_score": _average(scores),
        "sleep_score_min": score_min,
        "sleep_score_max": score_max,
        "avg_sleep_duration_minutes": _average([s.sleep_duration_minutes for s in snaps]),
        "avg_deep_minutes": _average([s.deep_minutes for s in snaps]),
        "avg_rem_minutes": _average([s.rem_minutes for s in snaps]),
        "avg_resting_hr": _average([s.resting_heart_rate for s in snaps]),
        "avg_breathing_rate": _average([s.breathing_rate for s in snaps]),
        "avg_spo2": _average([s.spo2 for s in snaps]),
        "sample_days": len(snaps),
    }


def _total_minutes_by_day(sessions: list[GameSession]) -> dict[date, float]:
    """
    Total plausible playtime per gaming day. Skips still-open sessions and the
    implausibly long ones that are really polling artifacts (see
    MAX_PLAUSIBLE_SESSION_MINUTES), so a wifi-drop doesn't inflate a day.
    """
    totals: dict[date, float] = {}
    for session in sessions:
        if session.duration_minutes is None or session.duration_minutes > MAX_PLAUSIBLE_SESSION_MINUTES:
            continue
        day = gaming_day(session.start_time)
        totals[day] = totals.get(day, 0.0) + session.duration_minutes
    return totals


def _last_session_end_by_day(sessions: list[GameSession]) -> dict[date, datetime]:
    """
    Latest session end per gaming day, skipping sessions that are still open
    (no end_time yet) or implausibly long (see MAX_PLAUSIBLE_SESSION_MINUTES).
    """
    last: dict[date, datetime] = {}
    for session in sessions:
        if session.end_time is None:
            continue
        if session.duration_minutes is not None and session.duration_minutes > MAX_PLAUSIBLE_SESSION_MINUTES:
            continue
        day = gaming_day(session.start_time)
        if day not in last or session.end_time > last[day]:
            last[day] = session.end_time
    return last


def _load(db: Session) -> tuple[list[GameSession], dict[date, HealthSnapshot]]:
    sessions = db.query(GameSession).all()
    snapshots = {snap.date: snap for snap in db.query(HealthSnapshot).all()}
    return sessions, snapshots


def _summarize(sessions: list[GameSession], snaps: list[HealthSnapshot]) -> dict:
    """Build the shared metric block for a group of sessions and their recovery days."""
    durations = [s.duration_minutes for s in sessions if s.duration_minutes is not None]
    resting_hrs = [s.resting_heart_rate for s in snaps]
    sleep_scores = [s.sleep_score for s in snaps]
    hr_min, hr_max = _spread(resting_hrs)
    score_min, score_max = _spread(sleep_scores)
    return {
        "session_count": len(sessions),
        "recovery_days": len(snaps),
        "avg_session_minutes": _average(durations),
        "avg_resting_hr": _average(resting_hrs),
        "resting_hr_min": hr_min,
        "resting_hr_max": hr_max,
        "avg_sleep_score": _average(sleep_scores),
        "sleep_score_min": score_min,
        "sleep_score_max": score_max,
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

    return {name: _bucket_stats(snaps) for name, snaps in buckets.items()}


def get_wind_down_impact(db: Session) -> dict:
    """
    Next-morning sleep bucketed by how long before bed the last session ended.
    Answers: "does stopping earlier actually help me sleep?"

    Note this is confounded with bedtime itself — short gaps usually mean late
    nights, and late nights mean less sleep regardless of the activity. Read it
    alongside get_late_night_impact rather than on its own.
    """
    sessions, snapshots = _load(db)
    last_end = _last_session_end_by_day(sessions)

    buckets: dict[str, list[tuple[HealthSnapshot, float]]] = {name: [] for name, _, _ in WIND_DOWN_BUCKETS}
    for day, end_time in last_end.items():
        snapshot = snapshots.get(recovery_date(day))
        # sleep_start is the bedtime that followed the session; without it
        # there's no gap to measure.
        if snapshot is None or snapshot.sleep_start is None:
            continue

        gap = (snapshot.sleep_start - end_time).total_seconds() / 60
        if gap < 0 or gap > MAX_WIND_DOWN_GAP_MINUTES:
            continue

        for name, low, high in WIND_DOWN_BUCKETS:
            if low <= gap < high:
                buckets[name].append((snapshot, gap))
                break

    return {
        name: {
            "avg_gap_minutes": _average([gap for _, gap in rows]),
            **_bucket_stats([snap for snap, _ in rows]),
        }
        for name, rows in buckets.items()
    }


def get_late_night_impact(db: Session) -> dict:
    """
    Next-morning sleep after late-night gaming vs earlier gaming vs no gaming.

    "Late" is measured against LATE_NIGHT_HOUR on the *gaming* day, so a session
    ending at 1am is correctly late (it's past 11pm on the previous evening)
    rather than looking like an early-morning session.
    """
    sessions, snapshots = _load(db)
    last_end = _last_session_end_by_day(sessions)
    # Days that had sessions but no usable end time — excluded entirely rather
    # than miscounted as "no gaming".
    all_gaming_days = {gaming_day(s.start_time) for s in sessions}

    buckets: dict[str, list[HealthSnapshot]] = {
        "late_night_gaming": [],
        "earlier_gaming": [],
        "no_gaming": [],
    }
    for snapshot in snapshots.values():
        day = snapshot.date - timedelta(days=1)
        end_time = last_end.get(day)

        if end_time is None:
            if day not in all_gaming_days:
                buckets["no_gaming"].append(snapshot)
            continue

        cutoff = datetime.combine(day, time(settings.LATE_NIGHT_HOUR))
        buckets["late_night_gaming" if end_time >= cutoff else "earlier_gaming"].append(snapshot)

    return {name: _bucket_stats(snaps) for name, snaps in buckets.items()}


def get_playtime_impact(db: Session) -> dict:
    """
    Next-morning recovery bucketed by how much was played that gaming day.
    Answers: "does a longer night cost more recovery?"
    """
    sessions, snapshots = _load(db)
    totals = _total_minutes_by_day(sessions)

    buckets: dict[str, list[tuple[HealthSnapshot, float]]] = {name: [] for name, _, _ in PLAYTIME_BUCKETS}
    for day, minutes in totals.items():
        snapshot = snapshots.get(recovery_date(day))
        if snapshot is None:
            continue
        for name, low, high in PLAYTIME_BUCKETS:
            if low <= minutes < high:
                buckets[name].append((snapshot, minutes))
                break

    return {
        name: {
            "avg_playtime_minutes": _average([minutes for _, minutes in rows]),
            **_bucket_stats([snap for snap, _ in rows]),
        }
        for name, rows in buckets.items()
    }


def get_activity_interaction(db: Session) -> dict:
    """
    Next-morning recovery split by whether a gaming day was also physically
    active. Answers: "does staying active offset the gaming hit?"

    A gaming day D's own activity lives on snapshot D (active_minutes for that
    calendar day); its recovery sleep is snapshot D+1. Gaming days whose activity
    we don't know (no snapshot / no active_minutes) are left out of the
    active/sedentary split rather than guessed — only the no-gaming bucket and
    the two known-activity buckets are honest.
    """
    sessions, snapshots = _load(db)
    gaming_days = {gaming_day(s.start_time) for s in sessions}
    threshold = settings.ACTIVE_MINUTES_THRESHOLD

    buckets: dict[str, list[HealthSnapshot]] = {
        "no_gaming": [],
        "gaming_active": [],
        "gaming_sedentary": [],
    }
    for snapshot in snapshots.values():
        day = snapshot.date - timedelta(days=1)  # gaming day whose sleep this snapshot holds
        if day not in gaming_days:
            buckets["no_gaming"].append(snapshot)
            continue

        day_snapshot = snapshots.get(day)
        active_minutes = day_snapshot.active_minutes if day_snapshot else None
        if active_minutes is None:
            continue  # unknown activity — don't force it into a bucket
        buckets["gaming_active" if active_minutes >= threshold else "gaming_sedentary"].append(snapshot)

    return {name: _bucket_stats(snaps) for name, snaps in buckets.items()}


def get_weekly_playtime_vs_sleep(db: Session) -> list[dict]:
    """
    Per-week total gaming minutes vs average next-morning sleep score, oldest
    first. Each week groups gaming days by their Monday; the sleep score is
    averaged over those gaming days' recovery nights, so playtime and the sleep
    it plausibly affected sit in the same bucket.
    """
    sessions, snapshots = _load(db)
    totals = _total_minutes_by_day(sessions)

    weeks: dict[date, dict] = {}
    for day, minutes in totals.items():
        week_start = day - timedelta(days=day.weekday())
        week = weeks.setdefault(week_start, {"minutes": 0.0, "scores": []})
        week["minutes"] += minutes
        snapshot = snapshots.get(recovery_date(day))
        if snapshot is not None and snapshot.sleep_score is not None:
            week["scores"].append(snapshot.sleep_score)

    return [
        {
            "week_start": week_start.isoformat(),
            "total_minutes": round(week["minutes"]),
            "avg_sleep_score": _average(week["scores"]),
        }
        for week_start, week in sorted(weeks.items())
    ]
