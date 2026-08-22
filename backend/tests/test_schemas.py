# Guards against schema/model drift.
#
# GameDetails once declared `name` while GameCache stores `game_name`. With
# from_attributes, Pydantic reads the attribute off the ORM object, so the
# mismatch only surfaced as a 500 at response time — never at import, never in
# a type check. These tests turn that class of bug into a failing test.

import pytest
from pydantic import BaseModel

from models.game_cache import GameCache
from models.health_snapshot import HealthSnapshot
from models.oauth_token import OAuthToken
from schemas.fitbit import HealthSnapshotResponse, TokenStatusResponse
from schemas.session import ActiveSessionResponse, GameSessionResponse  # noqa: F401
from schemas.steam import GameDetails


def assert_serializable(schema: type[BaseModel], instance) -> None:
    """Every field the schema declares must be readable off the ORM object."""
    missing = [name for name in schema.model_fields if not hasattr(instance, name)]
    assert not missing, f"{schema.__name__} declares fields absent from {type(instance).__name__}: {missing}"
    schema.model_validate(instance)


def test_game_details_matches_game_cache():
    game = GameCache(app_id=1, game_name="Brawlhalla", genre="Action", is_competitive=True)
    assert_serializable(GameDetails, game)


def test_health_snapshot_response_matches_model():
    from datetime import date

    snap = HealthSnapshot(date=date(2026, 8, 22), sleep_score=76)
    assert_serializable(HealthSnapshotResponse, snap)


def test_token_status_response_fields_are_all_returned():
    """
    fetch_token_status once omitted needs_reauth, so the endpoint always
    reported false — the schema defaults hid it.
    """
    from services.fitbit_service import fetch_token_status

    class _NoRow:
        def query(self, *_):
            return self

        def filter(self, *_):
            return self

        def first(self):
            return None

    returned = set(fetch_token_status(_NoRow()))
    declared = set(TokenStatusResponse.model_fields)
    assert declared <= returned, f"not returned by the service: {declared - returned}"


@pytest.mark.parametrize("schema", [GameSessionResponse, ActiveSessionResponse])
def test_session_schemas_expose_the_competitive_flag(schema):
    """
    is_competitive is the project's central variable; a session response that
    omits it can't answer the question the dashboard exists to ask.
    """
    assert "is_competitive" in schema.model_fields
