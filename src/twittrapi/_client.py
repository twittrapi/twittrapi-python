from __future__ import annotations

import asyncio
import time
from types import TracebackType
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    Iterator,
    Mapping,
    Optional,
    Set,
    Type,
)

import httpx

from . import _base
from ._base import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_RESPONSE_FORMAT,
    DEFAULT_TIMEOUT,
    ClientConfig,
    ResponseFormat,
    TimeoutTypes,
)
from ._endpoints import QueryValue
from ._exceptions import APIConnectionError, APITimeoutError, RateLimitError
from ._session import XSession
from .pagination import (
    extract_bottom_cursor,
    is_simple_page,
    page_is_empty,
    simple_next_cursor,
    unwrap_client_response,
)
from .resources import (
    Account,
    AsyncAccount,
    AsyncCommunities,
    AsyncLists,
    AsyncSearch,
    AsyncTrends,
    AsyncTweets,
    AsyncUsers,
    Communities,
    Lists,
    Search,
    Trends,
    Tweets,
    Users,
)

__all__ = ["TwittrAPI", "AsyncTwittrAPI", "DEFAULT_MAX_PAGES"]

DEFAULT_MAX_PAGES = 10


def _check_max_retries(max_retries: int) -> int:
    if isinstance(max_retries, bool) or not isinstance(max_retries, int) or max_retries < 0:
        raise ValueError("max_retries must be an integer >= 0")
    return max_retries


def _check_max_pages(max_pages: Optional[int]) -> None:
    if max_pages is not None and (
        isinstance(max_pages, bool) or not isinstance(max_pages, int) or max_pages < 1
    ):
        raise ValueError("max_pages must be a positive integer or None")


def _next_page_cursor(page: Any, response_format: ResponseFormat) -> Optional[str]:
    """The cursor to request next, or ``None`` to stop.

    Simple-format pages say it themselves (``nextCursor`` / ``hasNextPage``). Raw pages, and
    simple-format requests the API answered raw (routes without a simple format), fall back
    to the best-effort search for X's bottom cursor.
    """
    if response_format == "simple" and is_simple_page(page):
        return simple_next_cursor(page)
    # Account reads (/client/...) wrap X's JSON as {"status_code", "response": "<X body>"};
    # DM conversations answer {"has_more", "cursor", ...}.
    page = unwrap_client_response(page)
    if isinstance(page, dict) and isinstance(page.get("has_more"), bool) and "cursor" in page:
        cursor = page.get("cursor")
        return cursor if page["has_more"] and isinstance(cursor, str) and cursor else None
    next_cursor = extract_bottom_cursor(page)
    if not next_cursor or page_is_empty(page):
        return None
    return next_cursor


class _ClientMixin:
    _config: ClientConfig
    max_retries: int
    response_format: ResponseFormat
    session: Optional[XSession]

    @property
    def base_url(self) -> str:
        return self._config.base_url

    @property
    def auth_mode(self) -> str:
        """``"direct"`` (X-API-KEY header) or ``"rapidapi"`` (x-rapidapi-key header)."""
        return self._config.mode

    @property
    def rapidapi_host(self) -> Optional[str]:
        """The RapidAPI host sent as ``x-rapidapi-host``, or ``None`` in direct mode."""
        return self._config.rapidapi_host

    def _resolve_session(self, session: Optional[XSession]) -> XSession:
        """The session for an account action: the one passed to the call, else the client's."""
        resolved = session if session is not None else self.session
        if resolved is None:
            raise ValueError(
                "Account actions need an X session: pass session=XSession(cookie=..., "
                "proxy=...) to the client or to this call."
            )
        if not isinstance(resolved, XSession):
            raise TypeError(f"session must be an XSession, got {type(resolved).__name__}")
        return resolved

    def _resolve_format(self, response_format: Optional[ResponseFormat]) -> ResponseFormat:
        if response_format is None:
            return self.response_format
        return _base.check_response_format(response_format)

    def _request_args(
        self,
        path: str,
        params: Optional[Mapping[str, Optional[QueryValue]]],
        response_format: Optional[ResponseFormat] = None,
        body: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        fmt = self._resolve_format(response_format)
        args: Dict[str, Any] = {
            "url": _base.build_url(self._config, path),
            "params": _base.format_params(_base.clean_params(params or {}), fmt),
            "headers": _base.build_headers(self._config),
        }
        if body is not None:
            # httpx sets Content-Type: application/json.
            args["json"] = dict(body)
        return args

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(auth_mode={self.auth_mode!r}, base_url={self.base_url!r}, "
            + (f"rapidapi_host={self.rapidapi_host!r}, " if self.rapidapi_host else "")
            + f"response_format={self.response_format!r}"
            + (f", session={self.session!r}" if self.session is not None else "")
            + ")"
        )


class TwittrAPI(_ClientMixin):
    """Synchronous TwittrAPI client.

    Auth: pass ``api_key`` for the direct API (https://twittrapi.com) or ``rapidapi_key`` for
    RapidAPI. With neither, the ``TWITTRAPI_API_KEY`` and then ``RAPIDAPI_KEY`` environment
    variables are used. ``rapidapi_host`` (or ``RAPIDAPI_HOST``) selects the RapidAPI listing
    you subscribed to; the default is ``twitter-aio.p.rapidapi.com``.

    Every method returns the parsed JSON from the API. By default that is X's raw GraphQL
    response. With ``response_format="simple"`` (here for every call, or per call on any
    method) the API answers in its compact simple format (``{"data": ..., "nextCursor": ...,
    "hasNextPage": ...}`` with flat, camelCase tweets and users); parse it with
    :mod:`twittrapi.models` if you want typed objects.
    Requests that fail with 429, 5xx or a network error are retried ``max_retries`` times
    with exponential backoff. Other errors raise immediately.

    ``session`` (an :class:`~twittrapi.XSession`) is the X account that ``client.account``
    actions run as; it can also be passed per call as ``session=``. Read endpoints ignore it.

    Use it as a context manager, or call :meth:`close` when done.
    """

    users: Users
    tweets: Tweets
    search: Search
    lists: Lists
    communities: Communities
    trends: Trends
    account: Account

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        rapidapi_key: Optional[str] = None,
        rapidapi_host: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: TimeoutTypes = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: Optional[httpx.Client] = None,
        response_format: ResponseFormat = DEFAULT_RESPONSE_FORMAT,
        session: Optional[XSession] = None,
    ) -> None:
        self._config = _base.resolve_config(
            api_key, rapidapi_key, base_url, rapidapi_host=rapidapi_host
        )
        self.response_format = _base.check_response_format(response_format)
        if session is not None and not isinstance(session, XSession):
            raise TypeError(f"session must be an XSession, got {type(session).__name__}")
        self.session = session
        self.max_retries = _check_max_retries(max_retries)
        self.timeout = _base.make_timeout(timeout)
        self._owns_http = http_client is None
        self._http = http_client or httpx.Client(timeout=self.timeout)
        self._sleep: Callable[[float], None] = time.sleep

        self.users = Users(self)
        self.tweets = Tweets(self)
        self.search = Search(self)
        self.lists = Lists(self)
        self.communities = Communities(self)
        self.trends = Trends(self)
        self.account = Account(self)

    def _get(
        self,
        path: str,
        params: Optional[Mapping[str, Optional[QueryValue]]] = None,
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Sends a GET request with retries and returns the parsed JSON body."""
        return self._request("GET", path, params, None, response_format)

    def _post(
        self,
        path: str,
        params: Optional[Mapping[str, Optional[QueryValue]]] = None,
        body: Optional[Mapping[str, Any]] = None,
        *,
        response_format: Optional[ResponseFormat] = None,
        idempotent: bool = True,
    ) -> Any:
        """Sends a POST request with a JSON body, with the same retries as :meth:`_get`.
        With ``idempotent=False`` (actions that change something) only retries that cannot
        repeat the action are made, see :func:`_base.can_retry_error`."""
        return self._request("POST", path, params, body, response_format, idempotent)

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Mapping[str, Optional[QueryValue]]],
        body: Optional[Mapping[str, Any]],
        response_format: Optional[ResponseFormat],
        idempotent: bool = True,
    ) -> Any:
        args = self._request_args(path, params, response_format, body)
        attempt = 0
        while True:
            try:
                response = self._http.request(method, timeout=self.timeout, **args)
            except httpx.TimeoutException as exc:
                if attempt < self.max_retries and _base.can_retry_error(exc, idempotent):
                    self._sleep(_base.retry_delay(attempt))
                    attempt += 1
                    continue
                raise APITimeoutError(f"Request to TwittrAPI timed out: {exc}") from exc
            except httpx.TransportError as exc:
                if attempt < self.max_retries and _base.can_retry_error(exc, idempotent):
                    self._sleep(_base.retry_delay(attempt))
                    attempt += 1
                    continue
                raise APIConnectionError(f"Could not reach TwittrAPI: {exc}") from exc

            if attempt < self.max_retries and _base.should_retry_status(
                response.status_code, idempotent
            ):
                error = _base.make_status_error(response)
                retry_after = error.retry_after if isinstance(error, RateLimitError) else None
                self._sleep(_base.retry_delay(attempt, retry_after))
                attempt += 1
                continue
            return _base.process_response(response)

    def paginate(
        self,
        method: Callable[..., Any],
        *args: Any,
        max_pages: Optional[int] = DEFAULT_MAX_PAGES,
        **kwargs: Any,
    ) -> Iterator[Any]:
        """Calls a paginated method repeatedly and yields each page.

        ``method`` is any client method that takes ``cursor``, e.g. ``client.users.followers``.
        Other arguments are passed through. Pass ``cursor=`` to start from a saved cursor.

        In the simple format (the client's ``response_format``, or ``response_format=`` passed
        here for this iteration) each page's ``nextCursor`` is followed until ``hasNextPage``
        is false. In the raw format X's bottom cursor is followed; that detection is
        best-effort, see :mod:`twittrapi.pagination`.

        Stops when ``max_pages`` pages have been fetched (``None`` for no limit), when there
        is no next cursor, when the cursor repeats, or when a page has no results. Each page
        is a billed request.
        """
        _check_max_pages(max_pages)
        cursor: Optional[str] = kwargs.pop("cursor", None)
        fmt = self._resolve_format(kwargs.get("response_format"))
        seen: Set[str] = set()
        pages = 0
        while max_pages is None or pages < max_pages:
            page = method(*args, cursor=cursor, **kwargs)
            pages += 1
            yield page
            next_cursor = _next_page_cursor(page, fmt)
            if not next_cursor or next_cursor in seen or next_cursor == cursor:
                return
            seen.add(next_cursor)
            cursor = next_cursor

    def close(self) -> None:
        """Closes the underlying HTTP client (unless you passed your own ``http_client``)."""
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> "TwittrAPI":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self.close()


class AsyncTwittrAPI(_ClientMixin):
    """Asynchronous TwittrAPI client. Same arguments and methods as :class:`TwittrAPI`, but
    every API method is a coroutine and :meth:`paginate` is an async iterator.

    Use it as an async context manager, or call ``await client.aclose()`` when done.
    """

    users: AsyncUsers
    tweets: AsyncTweets
    search: AsyncSearch
    lists: AsyncLists
    communities: AsyncCommunities
    trends: AsyncTrends
    account: AsyncAccount

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        rapidapi_key: Optional[str] = None,
        rapidapi_host: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: TimeoutTypes = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: Optional[httpx.AsyncClient] = None,
        response_format: ResponseFormat = DEFAULT_RESPONSE_FORMAT,
        session: Optional[XSession] = None,
    ) -> None:
        self._config = _base.resolve_config(
            api_key, rapidapi_key, base_url, rapidapi_host=rapidapi_host
        )
        self.response_format = _base.check_response_format(response_format)
        if session is not None and not isinstance(session, XSession):
            raise TypeError(f"session must be an XSession, got {type(session).__name__}")
        self.session = session
        self.max_retries = _check_max_retries(max_retries)
        self.timeout = _base.make_timeout(timeout)
        self._owns_http = http_client is None
        self._http = http_client or httpx.AsyncClient(timeout=self.timeout)
        self._sleep: Callable[[float], Awaitable[None]] = asyncio.sleep

        self.users = AsyncUsers(self)
        self.tweets = AsyncTweets(self)
        self.search = AsyncSearch(self)
        self.lists = AsyncLists(self)
        self.communities = AsyncCommunities(self)
        self.trends = AsyncTrends(self)
        self.account = AsyncAccount(self)

    async def _get(
        self,
        path: str,
        params: Optional[Mapping[str, Optional[QueryValue]]] = None,
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        return await self._request("GET", path, params, None, response_format)

    async def _post(
        self,
        path: str,
        params: Optional[Mapping[str, Optional[QueryValue]]] = None,
        body: Optional[Mapping[str, Any]] = None,
        *,
        response_format: Optional[ResponseFormat] = None,
        idempotent: bool = True,
    ) -> Any:
        return await self._request("POST", path, params, body, response_format, idempotent)

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Mapping[str, Optional[QueryValue]]],
        body: Optional[Mapping[str, Any]],
        response_format: Optional[ResponseFormat],
        idempotent: bool = True,
    ) -> Any:
        args = self._request_args(path, params, response_format, body)
        attempt = 0
        while True:
            try:
                response = await self._http.request(method, timeout=self.timeout, **args)
            except httpx.TimeoutException as exc:
                if attempt < self.max_retries and _base.can_retry_error(exc, idempotent):
                    await self._sleep(_base.retry_delay(attempt))
                    attempt += 1
                    continue
                raise APITimeoutError(f"Request to TwittrAPI timed out: {exc}") from exc
            except httpx.TransportError as exc:
                if attempt < self.max_retries and _base.can_retry_error(exc, idempotent):
                    await self._sleep(_base.retry_delay(attempt))
                    attempt += 1
                    continue
                raise APIConnectionError(f"Could not reach TwittrAPI: {exc}") from exc

            if attempt < self.max_retries and _base.should_retry_status(
                response.status_code, idempotent
            ):
                error = _base.make_status_error(response)
                retry_after = error.retry_after if isinstance(error, RateLimitError) else None
                await self._sleep(_base.retry_delay(attempt, retry_after))
                attempt += 1
                continue
            return _base.process_response(response)

    async def paginate(
        self,
        method: Callable[..., Awaitable[Any]],
        *args: Any,
        max_pages: Optional[int] = DEFAULT_MAX_PAGES,
        **kwargs: Any,
    ) -> AsyncIterator[Any]:
        """Async version of :meth:`TwittrAPI.paginate`. Use with ``async for``."""
        _check_max_pages(max_pages)
        cursor: Optional[str] = kwargs.pop("cursor", None)
        fmt = self._resolve_format(kwargs.get("response_format"))
        seen: Set[str] = set()
        pages = 0
        while max_pages is None or pages < max_pages:
            page = await method(*args, cursor=cursor, **kwargs)
            pages += 1
            yield page
            next_cursor = _next_page_cursor(page, fmt)
            if not next_cursor or next_cursor in seen or next_cursor == cursor:
                return
            seen.add(next_cursor)
            cursor = next_cursor

    async def aclose(self) -> None:
        """Closes the underlying HTTP client (unless you passed your own ``http_client``)."""
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self) -> "AsyncTwittrAPI":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        await self.aclose()
