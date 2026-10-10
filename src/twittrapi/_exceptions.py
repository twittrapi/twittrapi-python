"""Exceptions raised by the TwittrAPI client.

Every exception the client raises on purpose is a subclass of :class:`TwittrAPIError`, so
``except twittrapi.TwittrAPIError`` catches all of them. HTTP errors carry the status code,
the message the API returned (``{"error": "..."}``) and the parsed body.
"""

from __future__ import annotations

from typing import Any, Optional

import httpx

__all__ = [
    "TwittrAPIError",
    "APIConnectionError",
    "APITimeoutError",
    "APIStatusError",
    "ValidationError",
    "AuthenticationError",
    "InsufficientBalanceError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
]


class TwittrAPIError(Exception):
    """Base class for all errors raised by this package."""

    message: str
    status_code: Optional[int]
    body: Any
    response: Optional[httpx.Response]

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        body: Any = None,
        response: Optional[httpx.Response] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.body = body
        self.response = response

    def __str__(self) -> str:
        if self.status_code is not None:
            return f"{self.message} (HTTP {self.status_code})"
        return self.message


class APIConnectionError(TwittrAPIError):
    """The request never got a response (DNS, connection refused, TLS, dropped connection)."""


class APITimeoutError(APIConnectionError):
    """The request timed out."""


class APIStatusError(TwittrAPIError):
    """The API answered with a 4xx or 5xx status. More specific subclasses exist for common codes."""

    status_code: int

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        body: Any = None,
        response: Optional[httpx.Response] = None,
    ) -> None:
        super().__init__(message, status_code=status_code, body=body, response=response)


class ValidationError(APIStatusError):
    """400 or 422: the API rejected the parameters."""


class AuthenticationError(APIStatusError):
    """401 or 403: the key is missing, invalid, or not allowed to make this call."""


class InsufficientBalanceError(APIStatusError):
    """402: the account has no balance left. Top up at https://twittrapi.com. Never retried."""


class NotFoundError(APIStatusError):
    """404: the user, tweet, list or community does not exist, is private, or is suspended."""


class RateLimitError(APIStatusError):
    """429: too many requests. ``retry_after`` is the server's suggested wait in seconds, if sent."""

    retry_after: Optional[float]

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 429,
        body: Any = None,
        response: Optional[httpx.Response] = None,
        retry_after: Optional[float] = None,
    ) -> None:
        super().__init__(message, status_code=status_code, body=body, response=response)
        self.retry_after = retry_after


class ServerError(APIStatusError):
    """5xx: something failed on the API side or upstream at X. Usually temporary."""
