from __future__ import annotations

import email.utils
import time

import httpx
import pytest

from twittrapi import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    InsufficientBalanceError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TwittrAPIError,
    ValidationError,
)
from twittrapi._base import parse_retry_after

from .conftest import MockAPI, json_response


@pytest.mark.parametrize(
    "status,exc",
    [
        (400, ValidationError),
        (401, AuthenticationError),
        (402, InsufficientBalanceError),
        (403, AuthenticationError),
        (404, NotFoundError),
        (409, APIStatusError),
        (422, ValidationError),
        (429, RateLimitError),
        (500, ServerError),
        (502, ServerError),
        (503, ServerError),
    ],
)
def test_status_mapping(status: int, exc: type) -> None:
    api = MockAPI(json_response({"error": f"boom {status}"}, status))
    client = api.client(max_retries=0)
    with pytest.raises(exc) as info:
        client.users.get_by_id(1)
    err = info.value
    assert isinstance(err, TwittrAPIError)
    assert isinstance(err, APIStatusError)
    assert err.status_code == status
    assert err.message == f"boom {status}"
    assert err.body == {"error": f"boom {status}"}
    assert err.response is not None
    assert str(err) == f"boom {status} (HTTP {status})"


def test_default_message_without_error_body() -> None:
    api = MockAPI(httpx.Response(402))
    with pytest.raises(InsufficientBalanceError, match="No balance"):
        api.client().users.get_by_id(1)


def test_plain_text_error_body() -> None:
    api = MockAPI(httpx.Response(500, text="Bad Gateway"))
    with pytest.raises(ServerError) as info:
        api.client(max_retries=0).users.get_by_id(1)
    assert info.value.message == "Bad Gateway"


def test_message_field_fallback() -> None:
    api = MockAPI(json_response({"message": "You are not subscribed to this API."}, 403))
    with pytest.raises(AuthenticationError, match="not subscribed"):
        api.client().users.get_by_id(1)


def test_rate_limit_retry_after_seconds() -> None:
    api = MockAPI(json_response({"error": "slow down"}, 429, {"Retry-After": "7"}))
    with pytest.raises(RateLimitError) as info:
        api.client(max_retries=0).users.get_by_id(1)
    assert info.value.retry_after == 7.0


def test_rate_limit_without_retry_after() -> None:
    api = MockAPI(json_response({"error": "slow down"}, 429))
    with pytest.raises(RateLimitError) as info:
        api.client(max_retries=0).users.get_by_id(1)
    assert info.value.retry_after is None


def test_parse_retry_after_http_date() -> None:
    date = email.utils.formatdate(time.time() + 30, usegmt=True)
    value = parse_retry_after(date)
    assert value is not None and 25 <= value <= 31
    assert parse_retry_after("garbage") is None
    assert parse_retry_after(None) is None
    assert parse_retry_after("-5") == 0.0


def test_non_json_success_raises() -> None:
    api = MockAPI(httpx.Response(200, text="<html>"))
    with pytest.raises(TwittrAPIError, match="Expected a JSON"):
        api.client().users.get_by_id(1)


def test_empty_success_body_returns_none() -> None:
    api = MockAPI(httpx.Response(200))
    assert api.client().users.get_by_id(1) is None


def test_connection_error_wrapped() -> None:
    api = MockAPI(httpx.ConnectError("refused"))
    with pytest.raises(APIConnectionError, match="Could not reach"):
        api.client(max_retries=0).users.get_by_id(1)


def test_timeout_wrapped() -> None:
    api = MockAPI(httpx.ReadTimeout("slow"))
    with pytest.raises(APITimeoutError):
        api.client(max_retries=0).users.get_by_id(1)


async def test_async_error_mapping() -> None:
    api = MockAPI(json_response({"error": "no balance"}, 402))
    with pytest.raises(InsufficientBalanceError, match="no balance"):
        await api.async_client().users.get_by_id(1)
