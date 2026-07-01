# ORM model for a gaming session.
# Each row represents one continuous play session detected by polling Steam.
# start_time is set when polling first detects the user playing a game,
# end_time is set when the user stops or switches games.

from sqlalchemy import Column, Integer, String, DateTime, Float
from database import Base


class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, nullable=False, index=True)
    game_name = Column(String, nullable=False)
    genre = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Float, nullable=True)
