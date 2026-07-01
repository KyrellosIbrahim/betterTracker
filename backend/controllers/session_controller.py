# Routes for game session data.
# Sessions are created by the background polling loop and stored in the DB.
# These endpoints let the frontend read session history.

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date, datetime, time
from database import get_db
from models.game_session import GameSession
from schemas.session import GameSessionResponse, ActiveSessionResponse

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("/", response_model=list[GameSessionResponse])
def get_sessions(
    target_date: date | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    """List game sessions, optionally filtered by date. Most recent first."""
    query = db.query(GameSession)

    if target_date:
        day_start = datetime.combine(target_date, time.min)
        day_end = datetime.combine(target_date, time.max)
        query = query.filter(GameSession.start_time.between(day_start, day_end))

    return query.order_by(GameSession.start_time.desc()).limit(limit).all()


@router.get("/active", response_model=ActiveSessionResponse | None)
def get_active_session(db: Session = Depends(get_db)):
    """Get the currently active game session, if one exists."""
    session = db.query(GameSession).filter(GameSession.end_time.is_(None)).first()
    if not session:
        return None

    elapsed = (datetime.now() - session.start_time).total_seconds() / 60
    return ActiveSessionResponse(
        game_id=session.game_id,
        game_name=session.game_name,
        genre=session.genre,
        start_time=session.start_time,
        elapsed_minutes=round(elapsed, 1),
    )


@router.delete("/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    """Delete a session by ID. Useful for removing bad/duplicate entries."""
    session = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not session:
        return {"error": "Session not found"}
    db.delete(session)
    db.commit()
    return {"status": "deleted"}
