# Pydantic schemas for game session data.
# Sessions are built by the polling loop and stored in the DB.

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GameSessionResponse(BaseModel):
    """A single completed game session."""
    model_config = {"from_attributes": True}

    id: int
    game_id: int
    game_name: str
    genre: Optional[str] = None
    is_competitive: bool = False
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[float] = None



class ActiveSessionResponse(BaseModel):
    """The currently active (in-progress) game session, if any."""
    game_id: int
    game_name: str
    genre: Optional[str] = None
    is_competitive: bool = False
    start_time: datetime
    elapsed_minutes: float
