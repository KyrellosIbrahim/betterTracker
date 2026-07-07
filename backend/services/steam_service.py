# Business logic for Steam API interactions.
# Handles polling for currently-playing status, manual game metadata lookups,
# and managing game session lifecycle (open, close, track duration).

import requests
from datetime import datetime
from sqlalchemy.orm import Session
from config import settings
from models.game_session import GameSession
from models.game_cache import GameCache


def get_currently_playing() -> dict:
    """Fetch the user's current player summary from Steam. Returns the raw player dict."""
    response = requests.get(settings.STEAM_GET_PLAYER_SUMMARIES_URL)
    response.raise_for_status()
    players = response.json()["response"]["players"]
    return players[0] if players else {}


def get_recently_played() -> dict:
    """Fetch the user's recently played games from Steam."""
    response = requests.get(settings.STEAM_GET_RECENTLY_PLAYED_GAMES_URL)
    response.raise_for_status()
    return response.json()["response"]


def get_game_metadata(app_id: int, db: Session) -> GameCache | None:
    """Look up a game's metadata from the manual cache. Returns None if the game hasn't been added yet."""
    result = db.query(GameCache).filter(GameCache.app_id == app_id).first()
    return result  # type: ignore[return-value]


def upsert_game(app_id: int, game_name: str, genre: str | None, is_competitive: bool, db: Session) -> GameCache:
    """Add or update a game in the cache."""
    existing = db.query(GameCache).filter(GameCache.app_id == app_id).first()
    if existing:
        existing.game_name = game_name
        existing.genre = genre
        existing.is_competitive = is_competitive
    else:
        existing = GameCache(
            app_id=app_id,
            game_name=game_name,
            genre=genre,
            is_competitive=is_competitive,
        )
        db.add(existing)
    db.commit()
    db.refresh(existing)
    return existing


def open_session(game_id: int, game_name: str, genre: str | None, is_competitive: bool, db: Session) -> GameSession:
    """Start a new game session when polling detects the user is playing."""
    session = GameSession(
        game_id=game_id,
        game_name=game_name,
        genre=genre,
        is_competitive=is_competitive,
        start_time=datetime.now(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def close_session(session: GameSession, db: Session) -> GameSession:
    """Close an active session when the user stops playing or switches games."""
    session.end_time = datetime.now()
    session.duration_minutes = (session.end_time - session.start_time).total_seconds() / 60
    db.commit()
    db.refresh(session)
    return session


def get_active_session(db: Session) -> GameSession | None:
    """Get the currently open (no end_time) game session, if one exists."""
    result = db.query(GameSession).filter(GameSession.end_time.is_(None)).first()
    return result  # type: ignore[return-value]
