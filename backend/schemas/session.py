# Pydantic schemas for game session data.
# Sessions are built by the polling loop and stored in the DB.

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GameSessionResponse(BaseModel):
    """A single completed game session."""
    id: int
    game_id: int
    game_name: str
    genre: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[float] = None

    class Config:
        from_attributes = True


class ActiveSessionResponse(BaseModel):
    """The currently active (in-progress) game session, if any."""
    game_id: int
    game_name: str
    genre: Optional[str] = None
    start_time: datetime
    elapsed_minutes: float
