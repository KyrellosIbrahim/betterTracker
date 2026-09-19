# Guards that a failed Steam request never leaks the API key into the exception
# message (and therefore into logs). The key rides in the URL query string, so
# requests embeds it in its errors — steam_service must scrub it at the source.

import pytest
import requests

from config import settings
from services import steam_service

FAKE_KEY = "DEADBEEF0123456789ABCDEF"


@pytest.fixture
def steam_key(monkeypatch):
    """Pin a known API key so we can assert it is redacted."""
    monkeypatch.setattr(settings, "STEAM_API_KEY", FAKE_KEY)
    return FAKE_KEY


def _raise_with_key(*args, **kwargs):
    # Mimics what requests puts in a real failure: the full URL, key included.
    raise requests.HTTPError(
        f"403 Client Error: Forbidden for url: "
        f"https://api.steampowered.com/x?key={FAKE_KEY}&steamids=123"
    )


@pytest.mark.parametrize("call", [
    steam_service.get_currently_playing,
    steam_service.get_recently_played,
])
def test_request_failure_redacts_api_key(call, steam_key, monkeypatch):
    monkeypatch.setattr(requests, "get", _raise_with_key)

    with pytest.raises(requests.RequestException) as exc_info:
        call()

    message = str(exc_info.value)
    assert FAKE_KEY not in message
    assert "***REDACTED***" in message
