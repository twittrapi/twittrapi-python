"""Official Python client for TwittrAPI (https://twittrapi.com), a read API for X (Twitter) data.

    from twittrapi import TwittrAPI

    client = TwittrAPI(api_key="...")
    user = client.users.get_by_username("jack")

Not affiliated with X Corp.
"""

from ._base import DEFAULT_BASE_URL, RAPIDAPI_BASE_URL, RAPIDAPI_HOST
from ._client import DEFAULT_MAX_PAGES, AsyncTwittrAPI, TwittrAPI
from ._exceptions import (
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
from ._endpoints import MAX_COUNT
from ._version import __version__
from .pagination import extract_bottom_cursor

__all__ = [
    "__version__",
    "TwittrAPI",
    "AsyncTwittrAPI",
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
    "extract_bottom_cursor",
    "DEFAULT_BASE_URL",
    "DEFAULT_MAX_PAGES",
    "MAX_COUNT",
    "RAPIDAPI_BASE_URL",
    "RAPIDAPI_HOST",
]
