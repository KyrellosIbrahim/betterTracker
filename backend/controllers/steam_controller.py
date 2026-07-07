# Routes for Steam API data and game metadata management.
# Exposes currently-playing status, recently played games,
# and CRUD for the manual game cache (genre + competitive flag).

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services import steam_service
from models.game_cache import GameCache
from schemas.steam import (
    CurrentlyPlayingResponse,
    RecentlyPlayedResponse,
    RecentlyPlayedGame,
    GameDetails,
    GameDetailsCreate,
)

router = APIRouter(prefix="/steam", tags=["Steam"])


@router.get("/currently-playing", response_model=CurrentlyPlayingResponse)
def get_currently_playing(db: Session = Depends(get_db)):
    """Check what the user is currently playing on Steam."""
    player = steam_service.get_currently_playing()

    game_id = player.get("gameid")
    if not game_id:
        return CurrentlyPlayingResponse(is_playing=False)

    game_id = int(game_id)
    game_name = player.get("gameextrainfo", "Unknown")
    metadata = steam_service.get_game_metadata(game_id, db)

    return CurrentlyPlayingResponse(
        is_playing=True,
        game_id=game_id,
        game_name=game_name,
        genre=metadata.genre if metadata else None,
        is_competitive=metadata.is_competitive if metadata else None,
    )


@router.get("/recently-played", response_model=RecentlyPlayedResponse)
def get_recently_played(db: Session = Depends(get_db)):
    """Get games played in the last 2 weeks with playtime and metadata."""
    data = steam_service.get_recently_played()
    games = []

    for game in data.get("games", []):
        metadata = steam_service.get_game_metadata(game["appid"], db)
        games.append(RecentlyPlayedGame(
            app_id=game["appid"],
            name=game["name"],
            playtime_2weeks=game.get("playtime_2weeks", 0),
            playtime_forever=game.get("playtime_forever", 0),
            genre=metadata.genre if metadata else None,
            is_competitive=metadata.is_competitive if metadata else None,
        ))

    return RecentlyPlayedResponse(total_count=len(games), games=games)


# --- Game Cache Management ---

@router.get("/games", response_model=list[GameDetails])
def list_games(db: Session = Depends(get_db)):
    """List all games in the cache with their genre and competitive flag."""
    return db.query(GameCache).all()


@router.post("/games", response_model=GameDetails)
def add_game(game: GameDetailsCreate, db: Session = Depends(get_db)):
    """Add or update a game in the cache."""
    return steam_service.upsert_game(
        app_id=game.app_id,
        game_name=game.game_name,
        genre=game.genre,
        is_competitive=game.is_competitive,
        db=db,
    )


@router.delete("/games/{app_id}")
def delete_game(app_id: int, db: Session = Depends(get_db)):
    """Remove a game from the cache."""
    game = db.query(GameCache).filter(GameCache.app_id == app_id).first()
    if not game:
        return {"error": "Game not found"}
    db.delete(game)
    db.commit()
    return {"status": "deleted"}
