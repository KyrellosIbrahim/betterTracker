# Business logic for Steam API interactions.
# Handles polling for currently-playing status, manual game metadata lookups,
# and managing game session lifecycle (open, close, track duration).

import requests
from datetime import datetime
from sqlalchemy.orm import Session
from config import settings
from models.game_session import GameSession
from models.game_cache import GameCache


def _get_json(url: str) -> dict:
    """GET a keyed Steam URL, redacting the API key from any failure message.

    The key rides in the URL query string, and requests embeds the full URL in
    its exceptions — so a raw error would leak the secret into the logs (the
    poller's warning, or a controller's 500 traceback). Re-raise with the key
    scrubbed; `from None` drops the original key-bearing message.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise requests.RequestException(settings.redact_secrets(str(e))) from None


def get_currently_playing() -> dict:
    """Fetch the user's current player summary from Steam. Returns the raw player dict."""
    players = _get_json(settings.STEAM_GET_PLAYER_SUMMARIES_URL)["response"]["players"]
    return players[0] if players else {}


def get_recently_played() -> dict:
    """Fetch the user's recently played games from Steam."""
    return _get_json(settings.STEAM_GET_RECENTLY_PLAYED_GAMES_URL)["response"]


def get_game_metadata(app_id: int, db: Session) -> GameCache | None:
    """Look up a game's metadata from the manual cache. Returns None if the game hasn't been added yet."""
    result = db.query(GameCache).filter(GameCache.app_id == app_id).first()
    return result  # type: ignore[return-value]


def upsert_game(app_id: int, game_name: str, genre: str | None, is_competitive: bool, db: Session) -> GameCache:
    """
    Add or update a game in the cache, and backfill its existing sessions.

    `is_competitive`/`genre` are denormalized onto each GameSession at capture
    time, and the insights group by that stored flag — so tagging a game here
    would have no effect on history unless we rewrite its past sessions too.
    Propagating keeps the session flag in sync with the cache, which is what
    makes a freshly-tagged game show up in the gaming-vs-recovery comparisons.
    """
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

    # Backfill past sessions of this game (game_id is the Steam app id).
    db.query(GameSession).filter(GameSession.game_id == app_id).update(
        {GameSession.is_competitive: is_competitive, GameSession.genre: genre},
        synchronize_session=False,
    )

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
