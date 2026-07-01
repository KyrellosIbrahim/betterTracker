# Business logic for Steam API interactions.
# Handles polling for currently-playing status, genre lookups via the Store API,
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


def get_game_genre(app_id: int, db: Session) -> str | None:
    """Look up a game's genre. Checks the local cache first, then hits the Steam Store API."""
    cached = db.query(GameCache).filter(GameCache.app_id == app_id).first()
    if cached:
        return cached.genre

    # Fetch from Steam Store API and cache the result
    response = requests.get(settings.STEAM_GET_GAME_DETAILS_URL(app_id))
    if response.status_code != 200:
        return None

    data = response.json()
    app_data = data.get(str(app_id), {}).get("data", {})
    genres = app_data.get("genres", [])
    genre_str = ", ".join(g["description"] for g in genres) if genres else None

    cache_entry = GameCache(
        app_id=app_id,
        game_name=app_data.get("name", "Unknown"),
        genre=genre_str,
        tags=None,
    )
    db.add(cache_entry)
    db.commit()

    return genre_str


def open_session(game_id: int, game_name: str, genre: str | None, db: Session) -> GameSession:
    """Start a new game session when polling detects the user is playing."""
    session = GameSession(
        game_id=game_id,
        game_name=game_name,
        genre=genre,
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
    return db.query(GameSession).filter(GameSession.end_time.is_(None)).first()
