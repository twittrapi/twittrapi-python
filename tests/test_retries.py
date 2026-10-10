from __future__ import annotations

import httpx
import pytest

from twittrapi import (
    APIConnectionError,
    InsufficientBalanceError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from twittrapi._base import MAX_RETRY_AFTER, retry_delay

from .conftest import MockAPI, json_response


def ok() -> httpx.Response:
    return json_response({"data": 1})


def test_retries_429_then_succeeds() -> None:
    api = MockAPI(json_response({"error": "rl"}, 429, {"Retry-After": "3"}), ok())
    assert api.client().users.get_by_id(1) == {"data": 1}
    assert len(api.requests) == 2
    assert api.sleeps == [3.0]


def test_retries_5xx_then_succeeds() -> None:
    api = MockAPI(json_response({"error": "x"}, 503), json_response({"error": "x"}, 500), ok())
    assert api.client().users.get_by_id(1) == {"data": 1}
    assert len(api.requests) == 3
    assert len(api.sleeps) == 2
    # exponential backoff with up to 25% jitter
    assert 0.5 <= api.sleeps[0] <= 0.625
    assert 1.0 <= api.sleeps[1] <= 1.25


def test_gives_up_after_max_retries() -> None:
    api = MockAPI(json_response({"error": "down"}, 502))
    with pytest.raises(ServerError):
        api.client(max_retries=2).users.get_by_id(1)
    assert len(api.requests) == 3


def test_max_retries_zero_means_one_attempt() -> None:
    api = MockAPI(json_response({"error": "rl"}, 429))
    with pytest.raises(RateLimitError):
        api.client(max_retries=0).users.get_by_id(1)
    assert len(api.requests) == 1
    assert api.sleeps == []


def test_custom_max_retries() -> None:
    api = MockAPI(json_response({"error": "down"}, 500))
    with pytest.raises(ServerError):
        api.client(max_retries=5).users.get_by_id(1)
    assert len(api.requests) == 6


@pytest.mark.parametrize(
    "status,exc",
    [(400, ValidationError), (402, InsufficientBalanceError), (404, NotFoundError), (422, ValidationError)],
)
def test_no_retry_for_other_4xx(status: int, exc: type) -> None:
    api = MockAPI(json_response({"error": "no"}, status), ok())
    with pytest.raises(exc):
        api.client().users.get_by_id(1)
    assert len(api.requests) == 1
    assert api.sleeps == []


def test_retries_network_errors() -> None:
    api = MockAPI(httpx.ConnectError("refused"), httpx.ReadTimeout("slow"), ok())
    assert api.client().users.get_by_id(1) == {"data": 1}
    assert len(api.requests) == 3


def test_network_error_exhausts_retries() -> None:
    api = MockAPI(httpx.ConnectError("refused"))
    with pytest.raises(APIConnectionError):
        api.client(max_retries=1).users.get_by_id(1)
    assert len(api.requests) == 2


def test_retry_after_is_capped() -> None:
    assert retry_delay(0, 3600) == MAX_RETRY_AFTER
    assert retry_delay(0, 2.5) == 2.5


def test_backoff_is_capped() -> None:
    assert retry_delay(20) <= 8.0 * 1.25


async def test_async_retries() -> None:
    api = MockAPI(json_response({"error": "rl"}, 429, {"Retry-After": "1"}), httpx.ConnectError("x"), ok())
    assert await api.async_client().users.get_by_id(1) == {"data": 1}
    assert len(api.requests) == 3
    assert api.sleeps[0] == 1.0


async def test_async_no_retry_on_402() -> None:
    api = MockAPI(json_response({"error": "no balance"}, 402), ok())
    with pytest.raises(InsufficientBalanceError):
        await api.async_client().users.get_by_id(1)
    assert len(api.requests) == 1
