# Importing every model here guarantees they're all registered on Base.metadata.
# Alembic's autogenerate compares the DB against that metadata, so a model that
# isn't imported anywhere would silently be missing from generated migrations.

from models.game_cache import GameCache
from models.game_session import GameSession
from models.health_snapshot import HealthSnapshot
from models.oauth_token import OAuthToken
from models.sleep_baseline import SleepBaseline

__all__ = ["GameCache", "GameSession", "HealthSnapshot", "OAuthToken", "SleepBaseline"]
