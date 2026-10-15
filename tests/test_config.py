from __future__ import annotations

import httpx
import pytest

import twittrapi
from twittrapi import AsyncTwittrAPI, TwittrAPI, TwittrAPIError

from .conftest import MockAPI


def test_direct_mode_url_and_headers(api: MockAPI) -> None:
    client = api.client(api_key="abc")
    client.users.get_by_username("jack")
    req = api.last
    assert str(req.url) == "https://api.twittrapi.com/user/by/username/jack"
    assert req.method == "GET"
    assert req.headers["X-API-KEY"] == "abc"
    assert "x-rapidapi-key" not in req.headers
    assert req.headers["Accept"] == "application/json"
    assert req.headers["User-Agent"] == f"twittrapi-python/{twittrapi.__version__}"
    assert client.auth_mode == "direct"


def test_rapidapi_mode_url_and_headers(api: MockAPI) -> None:
    client = api.client(api_key=None, rapidapi_key="rk")
    client.trends.get(1)
    req = api.last
    assert str(req.url) == "https://twitter-aio.p.rapidapi.com/trends/1"
    assert req.headers["x-rapidapi-key"] == "rk"
    assert req.headers["x-rapidapi-host"] == "twitter-aio.p.rapidapi.com"
    assert "X-API-KEY" not in req.headers
    assert client.auth_mode == "rapidapi"


def test_custom_base_url_strips_trailing_slash(api: MockAPI) -> None:
    client = api.client(base_url="http://localhost:8080/")
    client.users.get_by_id(12)
    assert str(api.last.url) == "http://localhost:8080/user/12"


def test_env_direct_key(api: MockAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TWITTRAPI_API_KEY", "env-key")
    monkeypatch.setenv("RAPIDAPI_KEY", "env-rapid")
    client = api.client(api_key=None)
    client.trends.locations()
    assert api.last.headers["X-API-KEY"] == "env-key"
    assert client.auth_mode == "direct"


def test_env_rapidapi_key(api: MockAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "env-rapid")
    client = api.client(api_key=None)
    client.trends.locations()
    assert api.last.headers["x-rapidapi-key"] == "env-rapid"
    assert str(api.last.url).startswith("https://twitter-aio.p.rapidapi.com/")


def test_explicit_rapidapi_key_beats_env_direct_key(
    api: MockAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TWITTRAPI_API_KEY", "env-key")
    client = api.client(api_key=None, rapidapi_key="rk")
    assert client.auth_mode == "rapidapi"


def test_env_base_url_applies_to_direct_mode(api: MockAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TWITTRAPI_BASE_URL", "https://staging.example.com")
    client = api.client()
    assert client.base_url == "https://staging.example.com"
    rapid = api.client(api_key=None, rapidapi_key="rk")
    assert rapid.base_url == "https://twitter-aio.p.rapidapi.com"


def test_missing_key_raises() -> None:
    with pytest.raises(TwittrAPIError, match="No API key"):
        TwittrAPI()
    with pytest.raises(TwittrAPIError, match="No API key"):
        AsyncTwittrAPI(api_key="   ")


def test_both_keys_rejected() -> None:
    with pytest.raises(ValueError):
        TwittrAPI(api_key="a", rapidapi_key="b")


def test_invalid_max_retries() -> None:
    with pytest.raises(ValueError):
        TwittrAPI(api_key="a", max_retries=-1)


def test_timeout_is_sent_per_request(api: MockAPI) -> None:
    seen = {}

    def reply(request: httpx.Request) -> httpx.Response:
        seen.update(request.extensions["timeout"])
        return httpx.Response(200, json={})

    api.replies = [reply]
    api.client(timeout=5).trends.locations()
    assert seen["read"] == 5


def test_context_manager_closes_own_client() -> None:
    with TwittrAPI(api_key="a") as client:
        assert not client._http.is_closed
    assert client._http.is_closed


def test_does_not_close_injected_client(api: MockAPI) -> None:
    client = api.client()
    client.close()
    assert not client._http.is_closed


async def test_async_context_manager() -> None:
    async with AsyncTwittrAPI(api_key="a") as client:
        assert not client._http.is_closed
    assert client._http.is_closed


async def test_async_rapidapi_headers(api: MockAPI) -> None:
    client = api.async_client(api_key=None, rapidapi_key="rk")
    await client.users.get_by_username("jack")
    assert str(api.last.url) == "https://twitter-aio.p.rapidapi.com/user/by/username/jack"
    assert api.last.headers["x-rapidapi-key"] == "rk"
    assert api.last.headers["x-rapidapi-host"] == "twitter-aio.p.rapidapi.com"


def test_repr_does_not_leak_key() -> None:
    assert "secret" not in repr(TwittrAPI(api_key="secret"))


def test_rapidapi_host_option(api: MockAPI) -> None:
    client = api.client(api_key=None, rapidapi_key="rk", rapidapi_host="twttr.p.rapidapi.com")
    client.trends.get(1)
    assert str(api.last.url) == "https://twttr.p.rapidapi.com/trends/1"
    assert api.last.headers["x-rapidapi-host"] == "twttr.p.rapidapi.com"
    assert client.rapidapi_host == "twttr.p.rapidapi.com"
    assert "rapidapi_host='twttr.p.rapidapi.com'" in repr(client)


def test_rapidapi_host_default(api: MockAPI) -> None:
    client = api.client(api_key=None, rapidapi_key="rk")
    assert client.rapidapi_host == twittrapi.RAPIDAPI_HOST == "twitter-aio.p.rapidapi.com"
    assert twittrapi.RAPIDAPI_BASE_URL == "https://twitter-aio.p.rapidapi.com"


def test_rapidapi_host_env(api: MockAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "env-rapid")
    monkeypatch.setenv("RAPIDAPI_HOST", "https://twttr.p.rapidapi.com/")
    client = api.client(api_key=None)
    client.trends.locations()
    assert str(api.last.url) == "https://twttr.p.rapidapi.com/misc/locations"
    assert api.last.headers["x-rapidapi-host"] == "twttr.p.rapidapi.com"


def test_rapidapi_host_option_beats_env(api: MockAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAPIDAPI_HOST", "env.p.rapidapi.com")
    client = api.client(api_key=None, rapidapi_key="rk", rapidapi_host="opt.p.rapidapi.com")
    assert client.rapidapi_host == "opt.p.rapidapi.com"


@pytest.mark.parametrize(
    "value",
    [
        "twttr.p.rapidapi.com",
        "https://twttr.p.rapidapi.com",
        "http://twttr.p.rapidapi.com/",
        "  twttr.p.rapidapi.com/  ",
        "HTTPS://Twttr.P.RapidAPI.com",
    ],
)
def test_rapidapi_host_normalized(value: str) -> None:
    client = TwittrAPI(rapidapi_key="rk", rapidapi_host=value)
    assert client.rapidapi_host == "twttr.p.rapidapi.com"
    assert client.base_url == "https://twttr.p.rapidapi.com"


@pytest.mark.parametrize(
    "value",
    [
        "twttr.p.rapidapi.com/v2",
        "https://twttr.p.rapidapi.com/x/",
        "twttr p.rapidapi.com",
        "https://",
    ],
)
def test_rapidapi_host_invalid(value: str) -> None:
    with pytest.raises(ValueError, match="rapidapi_host"):
        TwittrAPI(rapidapi_key="rk", rapidapi_host=value)


def test_invalid_rapidapi_host_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAPIDAPI_HOST", "twttr.p.rapidapi.com/path")
    with pytest.raises(ValueError, match="rapidapi_host"):
        AsyncTwittrAPI(rapidapi_key="rk")


def test_base_url_beats_rapidapi_host(api: MockAPI) -> None:
    client = api.client(
        api_key=None,
        rapidapi_key="rk",
        rapidapi_host="twttr.p.rapidapi.com",
        base_url="http://localhost:8080/",
    )
    client.trends.get(1)
    assert str(api.last.url) == "http://localhost:8080/trends/1"
    assert api.last.headers["x-rapidapi-host"] == "twttr.p.rapidapi.com"


def test_direct_mode_ignores_rapidapi_host(api: MockAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAPIDAPI_HOST", "not a host/")
    client = api.client(rapidapi_host="twttr.p.rapidapi.com")
    client.trends.get(1)
    assert str(api.last.url) == "https://api.twittrapi.com/trends/1"
    assert "x-rapidapi-host" not in api.last.headers
    assert client.rapidapi_host is None
    assert "rapidapi_host" not in repr(client)


async def test_async_rapidapi_host(api: MockAPI) -> None:
    client = api.async_client(api_key=None, rapidapi_key="rk", rapidapi_host="twttr.p.rapidapi.com")
    await client.trends.get(1)
    assert str(api.last.url) == "https://twttr.p.rapidapi.com/trends/1"
    assert api.last.headers["x-rapidapi-host"] == "twttr.p.rapidapi.com"
