# ORM model for manually maintained game metadata.
# Genre and competitive flag are set by the user, not fetched from Steam.
# This lets you tag games with what actually matters for health correlation
# (e.g. Brawlhalla ranked = competitive, RuneScape bossing = not).

from sqlalchemy import Column, Integer, String, Boolean
from database import Base


class GameCache(Base):
    __tablename__ = "game_cache"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, unique=True, nullable=False, index=True)
    game_name = Column(String, nullable=False)
    genre = Column(String, nullable=True)
    is_competitive = Column(Boolean, default=False, nullable=False)
