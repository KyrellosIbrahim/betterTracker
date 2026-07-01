# Routes for Steam API data.
# Exposes currently-playing status and recently played games.

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services import steam_service
from schemas.steam import CurrentlyPlayingResponse, RecentlyPlayedResponse, RecentlyPlayedGame

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
    genre = steam_service.get_game_genre(game_id, db)

    return CurrentlyPlayingResponse(
        is_playing=True,
        game_id=game_id,
        game_name=game_name,
        genre=genre,
    )


@router.get("/recently-played", response_model=RecentlyPlayedResponse)
def get_recently_played(db: Session = Depends(get_db)):
    """Get games played in the last 2 weeks with playtime and genre."""
    data = steam_service.get_recently_played()
    games = []

    for game in data.get("games", []):
        genre = steam_service.get_game_genre(game["appid"], db)
        games.append(RecentlyPlayedGame(
            app_id=game["appid"],
            name=game["name"],
            playtime_2weeks=game.get("playtime_2weeks", 0),
            playtime_forever=game.get("playtime_forever", 0),
            genre=genre,
        ))

    return RecentlyPlayedResponse(total_count=len(games), games=games)
