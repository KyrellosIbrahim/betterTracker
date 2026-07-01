# ORM model for cached game metadata from the Steam Store API.
# Genre lookups are expensive and don't change, so we cache them.
# Once a game's genre is fetched, it's stored here and never re-fetched.

from sqlalchemy import Column, Integer, String
from database import Base


class GameCache(Base):
    __tablename__ = "game_cache"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, unique=True, nullable=False, index=True)
    game_name = Column(String, nullable=False)
    genre = Column(String, nullable=True)
    tags = Column(String, nullable=True)
