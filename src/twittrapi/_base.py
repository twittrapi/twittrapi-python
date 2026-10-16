"""Shared logic for the sync and async clients: configuration, request building, error
mapping and retry timing. Nothing in here does I/O."""

from __future__ import annotations

import email.utils
import json
import os
import random
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, Literal, Mapping, Optional, Union, cast

import httpx

from ._endpoints import QueryValue
from ._exceptions import (
    APIStatusError,
    AuthenticationError,
    InsufficientBalanceError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TwittrAPIError,
    ValidationError,
)
from ._version import __version__

DEFAULT_BASE_URL = "https://api.twittrapi.com"
RAPIDAPI_HOST = "twitter-aio.p.rapidapi.com"
RAPIDAPI_BASE_URL = f"https://{RAPIDAPI_HOST}"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 2

# Backoff for retries without a Retry-After header: 0.5s, 1s, 2s, ... capped, plus jitter.
INITIAL_RETRY_DELAY = 0.5
MAX_RETRY_DELAY = 8.0
# Upper bound for honoring a server-sent Retry-After, so a bad header cannot stall a script.
MAX_RETRY_AFTER = 60.0

ENV_API_KEY = "TWITTRAPI_API_KEY"
ENV_RAPIDAPI_KEY = "RAPIDAPI_KEY"
ENV_BASE_URL = "TWITTRAPI_BASE_URL"
ENV_RAPIDAPI_HOST = "RAPIDAPI_HOST"

USER_AGENT = f"twittrapi-python/{__version__}"

TimeoutTypes = Union[float, httpx.Timeout, None]

ResponseFormat = Literal["raw", "simple"]
"""``"raw"``: X's JSON exactly as X sends it (the default). ``"simple"``: the API's compact,
camelCase format (``format=simple``), see https://twittrapi.com/docs/simple-format."""

RESPONSE_FORMATS = ("raw", "simple")
DEFAULT_RESPONSE_FORMAT: ResponseFormat = "raw"
FORMAT_PARAM = "format"


def check_response_format(value: Any, name: str = "response_format") -> ResponseFormat:
    if value not in RESPONSE_FORMATS:
        raise ValueError(f"{name} must be \"raw\" or \"simple\", got {value!r}")
    return cast(ResponseFormat, value)


@dataclass(frozen=True)
class ClientConfig:
    mode: str  # "direct" or "rapidapi"
    api_key: str
    base_url: str
    rapidapi_host: Optional[str] = None  # set in RapidAPI mode only

    @property
    def is_rapidapi(self) -> bool:
        return self.mode == "rapidapi"


def _clean(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value or None


_SCHEME = re.compile(r"^https?://", re.IGNORECASE)
_HOST = re.compile(r"^[A-Za-z0-9.-]+(:[0-9]+)?$")


def normalize_rapidapi_host(value: str) -> str:
    """Accepts ``twttr.p.rapidapi.com``, ``https://twttr.p.rapidapi.com`` or either with a
    trailing slash and returns the bare host. Anything with a path or spaces is rejected."""
    host = _SCHEME.sub("", value.strip()).rstrip("/")
    if not _HOST.match(host):
        raise ValueError(
            f"rapidapi_host must be a host name like \"twitter-aio.p.rapidapi.com\", got {value!r}"
        )
    return host.lower()


def resolve_config(
    api_key: Optional[str],
    rapidapi_key: Optional[str],
    base_url: Optional[str],
    env: Optional[Mapping[str, str]] = None,
    rapidapi_host: Optional[str] = None,
) -> ClientConfig:
    """Picks the auth mode. Explicit arguments win over environment variables; within each,
    the direct key wins over the RapidAPI key."""
    env = os.environ if env is None else env
    api_key = _clean(api_key)
    rapidapi_key = _clean(rapidapi_key)

    if api_key and rapidapi_key:
        raise ValueError("Pass either api_key or rapidapi_key, not both.")

    mode: Optional[str] = None
    key: Optional[str] = None
    if api_key:
        mode, key = "direct", api_key
    elif rapidapi_key:
        mode, key = "rapidapi", rapidapi_key
    elif _clean(env.get(ENV_API_KEY)):
        mode, key = "direct", _clean(env.get(ENV_API_KEY))
    elif _clean(env.get(ENV_RAPIDAPI_KEY)):
        mode, key = "rapidapi", _clean(env.get(ENV_RAPIDAPI_KEY))

    if not mode or not key:
        raise TwittrAPIError(
            "No API key found. Pass api_key=... (direct API, get one at https://twittrapi.com) "
            "or rapidapi_key=... (RapidAPI), or set the TWITTRAPI_API_KEY or RAPIDAPI_KEY "
            "environment variable."
        )

    # The RapidAPI host picks the listing (same paths on every listing). Direct mode ignores it.
    host: Optional[str] = None
    if mode == "rapidapi":
        raw_host = _clean(rapidapi_host) or _clean(env.get(ENV_RAPIDAPI_HOST))
        host = normalize_rapidapi_host(raw_host) if raw_host else RAPIDAPI_HOST

    url = _clean(base_url)
    if url is None and mode == "direct":
        url = _clean(env.get(ENV_BASE_URL))
    if url is None:
        url = f"https://{host}" if host else DEFAULT_BASE_URL
    return ClientConfig(mode=mode, api_key=key, base_url=url.rstrip("/"), rapidapi_host=host)


def build_headers(config: ClientConfig) -> Dict[str, str]:
    headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    if config.is_rapidapi:
        headers["x-rapidapi-key"] = config.api_key
        headers["x-rapidapi-host"] = config.rapidapi_host or RAPIDAPI_HOST
    else:
        headers["X-API-KEY"] = config.api_key
    return headers


def build_url(config: ClientConfig, path: str) -> str:
    return config.base_url + (path if path.startswith("/") else "/" + path)


def clean_params(params: Mapping[str, Optional[QueryValue]]) -> Dict[str, QueryValue]:
    return {k: v for k, v in params.items() if v is not None and v != ""}


def format_params(
    params: Dict[str, QueryValue], response_format: ResponseFormat
) -> Dict[str, QueryValue]:
    """Adds ``format=simple`` for the simple format. Raw requests are sent exactly as before
    (no ``format`` parameter), so their responses do not change."""
    if response_format == "simple":
        params = {**params, FORMAT_PARAM: "simple"}
    return params


def make_timeout(timeout: TimeoutTypes) -> httpx.Timeout:
    if isinstance(timeout, httpx.Timeout):
        return timeout
    return httpx.Timeout(timeout)


# ---------------------------------------------------------------------------
# Responses and errors
# ---------------------------------------------------------------------------


def _parse_body(response: httpx.Response) -> Any:
    text = response.text
    if not text.strip():
        return None
    try:
        return json.loads(text)
    except ValueError:
        return text


def _error_text(body: Any) -> Optional[str]:
    if isinstance(body, dict):
        for key in ("error", "message", "detail"):
            value = body.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    if isinstance(body, str) and body.strip():
        text = body.strip()
        return text if len(text) <= 500 else text[:500] + "..."
    return None


def parse_retry_after(value: Optional[str]) -> Optional[float]:
    """Parses a Retry-After header given in seconds or as an HTTP date."""
    if not value:
        return None
    value = value.strip()
    try:
        seconds = float(value)
    except ValueError:
        try:
            parsed = email.utils.parsedate_to_datetime(value)
        except (TypeError, ValueError, IndexError):
            return None
        if parsed is None:
            return None
        seconds = parsed.timestamp() - time.time()
    return max(seconds, 0.0)


_DEFAULT_MESSAGES = {
    400: "Bad request. Check the parameters you passed.",
    401: "Authentication failed. Check your API key.",
    402: "No balance left on this TwittrAPI account. Top up at https://twittrapi.com.",
    403: "Access denied. The key may not have access to this endpoint, or X refused the request.",
    404: "Not found. The user, tweet, list or community may not exist, be private, or be suspended.",
    422: "Invalid input. Check the IDs and parameters you passed.",
    429: "Rate limit hit. Wait before retrying.",
}


def make_status_error(response: httpx.Response) -> APIStatusError:
    status = response.status_code
    body = _parse_body(response)
    detail = _error_text(body)
    if detail:
        message = detail
    elif status in _DEFAULT_MESSAGES:
        message = _DEFAULT_MESSAGES[status]
    elif status >= 500:
        message = "TwittrAPI or X returned a server error. This is usually temporary."
    else:
        message = f"Request failed with status {status}."

    kwargs: Dict[str, Any] = {"status_code": status, "body": body, "response": response}
    if status in (400, 422):
        return ValidationError(message, **kwargs)
    if status in (401, 403):
        return AuthenticationError(message, **kwargs)
    if status == 402:
        return InsufficientBalanceError(message, **kwargs)
    if status == 404:
        return NotFoundError(message, **kwargs)
    if status == 429:
        retry_after = parse_retry_after(response.headers.get("retry-after"))
        return RateLimitError(message, retry_after=retry_after, **kwargs)
    if status >= 500:
        return ServerError(message, **kwargs)
    return APIStatusError(message, **kwargs)


def process_response(response: httpx.Response) -> Any:
    """Returns the parsed JSON body, or raises the matching exception for an error status."""
    if response.status_code >= 400:
        raise make_status_error(response)
    body = _parse_body(response)
    if isinstance(body, str):
        raise TwittrAPIError(
            "Expected a JSON response but got something else.",
            status_code=response.status_code,
            body=body,
            response=response,
        )
    return body


# ---------------------------------------------------------------------------
# Retries
# ---------------------------------------------------------------------------


def should_retry_status(status: int, idempotent: bool = True) -> bool:
    """429 and 5xx are retried. For actions that change something (``idempotent=False``)
    only 429 is: a 5xx can come after the action already happened."""
    if not idempotent:
        return status == 429
    return status == 429 or status >= 500


# Errors raised before the request was sent, so retrying cannot repeat an action.
_NOT_SENT_ERRORS = (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout)


def can_retry_error(exc: Exception, idempotent: bool = True) -> bool:
    """Whether a timeout or network error may be retried. Reads always may; actions that
    change something only when the connection was never made."""
    return idempotent or isinstance(exc, _NOT_SENT_ERRORS)


def retry_delay(attempt: int, retry_after: Optional[float] = None) -> float:
    """Seconds to wait before retry number ``attempt + 1`` (attempt starts at 0)."""
    if retry_after is not None:
        return min(retry_after, MAX_RETRY_AFTER)
    base: float = min(INITIAL_RETRY_DELAY * (2**attempt), MAX_RETRY_DELAY)
    return base * (1 + random.uniform(0, 0.25))
