"""Official Python client for TwittrAPI (https://twittrapi.com), an API for X (Twitter) data and account actions.

    from twittrapi import TwittrAPI

    client = TwittrAPI(api_key="...")
    user = client.users.get_by_username("jack")

    # Compact, camelCase JSON instead of X's raw GraphQL (opt-in, per client or per call):
    simple = TwittrAPI(api_key="...", response_format="simple")
    user = client.users.get_by_username("jack", response_format="simple")

    # Actions with your own X account (post, like, follow, DMs, ...):
    me = TwittrAPI(api_key="...", session=XSession(cookie="auth_token=...; ct0=...",
                                                   proxy="http://user:pass@host:port"))
    me.account.create_tweet("Hello")

Not affiliated with X Corp.
"""

from ._account_endpoints import Birthdate, ReplySettings, ReportReason
from ._base import DEFAULT_BASE_URL, RAPIDAPI_BASE_URL, RAPIDAPI_HOST, ResponseFormat
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
from ._session import XSession
from ._version import __version__
from .pagination import extract_bottom_cursor, simple_next_cursor, unwrap_client_response

__all__ = [
    "__version__",
    "TwittrAPI",
    "AsyncTwittrAPI",
    "XSession",
    "Birthdate",
    "ReplySettings",
    "ReportReason",
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
    "simple_next_cursor",
    "unwrap_client_response",
    "ResponseFormat",
    "DEFAULT_BASE_URL",
    "DEFAULT_MAX_PAGES",
    "MAX_COUNT",
    "RAPIDAPI_BASE_URL",
    "RAPIDAPI_HOST",
]
