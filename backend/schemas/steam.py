# Pydantic schemas for Steam API request/response validation.
# These define the shape of data going in and out of Steam-related endpoints.

from pydantic import BaseModel
from typing import Optional


class CurrentlyPlayingResponse(BaseModel):
    """Response for the /steam/currently-playing endpoint."""
    is_playing: bool
    game_id: Optional[int] = None
    game_name: Optional[str] = None
    genre: Optional[str] = None


class RecentlyPlayedGame(BaseModel):
    """A single game from the recently played list."""
    app_id: int
    name: str
    playtime_2weeks: int  # minutes
    playtime_forever: int  # minutes
    genre: Optional[str] = None


class RecentlyPlayedResponse(BaseModel):
    """Response for the /steam/recently-played endpoint."""
    total_count: int
    games: list[RecentlyPlayedGame]


class GameDetails(BaseModel):
    """Cached game metadata from the Steam Store API."""
    app_id: int
    name: str
    genre: Optional[str] = None
    tags: Optional[str] = None
