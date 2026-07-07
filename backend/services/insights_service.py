# Business logic for correlating Steam session data with Fitbit health data.
# Aggregates health metrics grouped by game genre and competitive flag to
# surface patterns like "sleep quality drops after late-night competitive gaming."

from sqlalchemy.orm import Session
from sqlalchemy import func
from models.game_session import GameSession
from models.health_snapshot import HealthSnapshot


def get_health_by_genre(db: Session) -> list[dict]:
    """
    Aggregate average health metrics for each game genre.
    Joins game sessions to health snapshots by matching session date to snapshot date.
    """
    results = (
        db.query(
            GameSession.genre,
            func.count(GameSession.id).label("session_count"),
            func.avg(GameSession.duration_minutes).label("avg_session_minutes"),
            func.avg(HealthSnapshot.resting_heart_rate).label("avg_resting_hr"),
            func.avg(HealthSnapshot.sleep_score).label("avg_sleep_score"),
            func.avg(HealthSnapshot.breathing_rate).label("avg_breathing_rate"),
        )
        .join(
            HealthSnapshot,
            func.date(GameSession.start_time) == HealthSnapshot.date,
        )
        .filter(GameSession.genre.isnot(None))
        .group_by(GameSession.genre)
        .all()
    )

    return [
        {
            "genre": row.genre,
            "session_count": row.session_count,
            "avg_session_minutes": round(row.avg_session_minutes, 1) if row.avg_session_minutes else None,
            "avg_resting_hr": round(row.avg_resting_hr, 1) if row.avg_resting_hr else None,
            "avg_sleep_score": round(row.avg_sleep_score, 1) if row.avg_sleep_score else None,
            "avg_breathing_rate": round(row.avg_breathing_rate, 1) if row.avg_breathing_rate else None,
        }
        for row in results
    ]


def get_sleep_impact_by_genre(db: Session) -> list[dict]:
    """
    Compare sleep scores on gaming days vs non-gaming days, broken down by genre.
    Helps answer: "Do I sleep worse after playing competitive games?"
    """
    # Sleep on days with gaming sessions, grouped by genre
    gaming_sleep = (
        db.query(
            GameSession.genre,
            func.avg(HealthSnapshot.sleep_score).label("avg_sleep_score"),
            func.count(HealthSnapshot.id).label("day_count"),
        )
        .join(
            HealthSnapshot,
            func.date(GameSession.start_time) == HealthSnapshot.date,
        )
        .filter(GameSession.genre.isnot(None))
        .group_by(GameSession.genre)
        .all()
    )

    return [
        {
            "genre": row.genre,
            "avg_sleep_score_on_gaming_days": round(row.avg_sleep_score, 1) if row.avg_sleep_score else None,
            "sample_days": row.day_count,
        }
        for row in gaming_sleep
    ]


def get_health_by_competitive(db: Session) -> list[dict]:
    """
    Aggregate average health metrics for competitive vs non-competitive sessions.
    The core thesis of the project: does competitive gaming hurt recovery?
    """
    results = (
        db.query(
            GameSession.is_competitive,
            func.count(GameSession.id).label("session_count"),
            func.avg(GameSession.duration_minutes).label("avg_session_minutes"),
            func.avg(HealthSnapshot.resting_heart_rate).label("avg_resting_hr"),
            func.avg(HealthSnapshot.sleep_score).label("avg_sleep_score"),
            func.avg(HealthSnapshot.breathing_rate).label("avg_breathing_rate"),
        )
        .join(
            HealthSnapshot,
            func.date(GameSession.start_time) == HealthSnapshot.date,
        )
        .group_by(GameSession.is_competitive)
        .all()
    )

    return [
        {
            "is_competitive": bool(row.is_competitive),
            "session_count": row.session_count,
            "avg_session_minutes": round(row.avg_session_minutes, 1) if row.avg_session_minutes else None,
            "avg_resting_hr": round(row.avg_resting_hr, 1) if row.avg_resting_hr else None,
            "avg_sleep_score": round(row.avg_sleep_score, 1) if row.avg_sleep_score else None,
            "avg_breathing_rate": round(row.avg_breathing_rate, 1) if row.avg_breathing_rate else None,
        }
        for row in results
    ]


def get_sleep_impact_by_competitive(db: Session) -> dict:
    """
    Compare sleep scores across three kinds of days: days with at least one
    competitive session, days with only casual sessions, and days with no gaming.
    """
    # Classify each gaming day by whether any session that day was competitive
    day_rows = (
        db.query(
            func.date(GameSession.start_time).label("day"),
            func.max(GameSession.is_competitive).label("had_competitive"),
        )
        .group_by("day")
        .all()
    )
    competitive_days = {row.day for row in day_rows if row.had_competitive}
    casual_days = {row.day for row in day_rows if not row.had_competitive}

    buckets: dict[str, list[int]] = {"competitive_days": [], "casual_only_days": [], "no_gaming_days": []}
    snapshots = db.query(HealthSnapshot).filter(HealthSnapshot.sleep_score.isnot(None)).all()
    for snap in snapshots:
        day = snap.date.isoformat()
        if day in competitive_days:
            buckets["competitive_days"].append(snap.sleep_score)
        elif day in casual_days:
            buckets["casual_only_days"].append(snap.sleep_score)
        else:
            buckets["no_gaming_days"].append(snap.sleep_score)

    return {
        name: {
            "avg_sleep_score": round(sum(scores) / len(scores), 1) if scores else None,
            "sample_days": len(scores),
        }
        for name, scores in buckets.items()
    }
