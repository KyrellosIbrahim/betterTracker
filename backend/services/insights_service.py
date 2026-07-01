# Business logic for correlating Steam session data with Fitbit health data.
# Aggregates health metrics grouped by game genre to surface patterns
# like "sleep quality drops after late-night competitive gaming."

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
