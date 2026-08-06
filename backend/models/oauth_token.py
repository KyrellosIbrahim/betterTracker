# ORM model for persisted OAuth tokens.
# One row per provider, so tokens survive server restarts instead of
# living only in memory.

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from database import Base


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, unique=True, nullable=False, index=True)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    needs_reauth = Column(Boolean, default=False, nullable=False)
    last_error = Column(String, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
