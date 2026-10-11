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
from .pagination import extract_bottom_cursor, is_simple_page, page_is_empty, simple_next_cursor
from .resources import (
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
    next_cursor = extract_bottom_cursor(page)
    if not next_cursor or page_is_empty(page):
        return None
    return next_cursor


class _ClientMixin:
    _config: ClientConfig
    max_retries: int
    response_format: ResponseFormat

    @property
    def base_url(self) -> str:
        return self._config.base_url

    @property
    def auth_mode(self) -> str:
        """``"direct"`` (X-API-KEY header) or ``"rapidapi"`` (x-rapidapi-key header)."""
        return self._config.mode

    def _resolve_format(self, response_format: Optional[ResponseFormat]) -> ResponseFormat:
        if response_format is None:
            return self.response_format
        return _base.check_response_format(response_format)

    def _request_args(
        self,
        path: str,
        params: Optional[Mapping[str, Optional[QueryValue]]],
        response_format: Optional[ResponseFormat] = None,
    ) -> Dict[str, Any]:
        fmt = self._resolve_format(response_format)
        return {
            "url": _base.build_url(self._config, path),
            "params": _base.format_params(_base.clean_params(params or {}), fmt),
            "headers": _base.build_headers(self._config),
        }

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(auth_mode={self.auth_mode!r}, base_url={self.base_url!r}, "
            f"response_format={self.response_format!r})"
        )


class TwittrAPI(_ClientMixin):
    """Synchronous TwittrAPI client.

    Auth: pass ``api_key`` for the direct API (https://twittrapi.com) or ``rapidapi_key`` for
    RapidAPI. With neither, the ``TWITTRAPI_API_KEY`` and then ``RAPIDAPI_KEY`` environment
    variables are used.

    Every method returns the parsed JSON from the API. By default that is X's raw GraphQL
    response. With ``response_format="simple"`` (here for every call, or per call on any
    method) the API answers in its compact simple format (``{"data": ..., "nextCursor": ...,
    "hasNextPage": ...}`` with flat, camelCase tweets and users); parse it with
    :mod:`twittrapi.models` if you want typed objects.
    Requests that fail with 429, 5xx or a network error are retried ``max_retries`` times
    with exponential backoff. Other errors raise immediately.

    Use it as a context manager, or call :meth:`close` when done.
    """

    users: Users
    tweets: Tweets
    search: Search
    lists: Lists
    communities: Communities
    trends: Trends

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        rapidapi_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: TimeoutTypes = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: Optional[httpx.Client] = None,
        response_format: ResponseFormat = DEFAULT_RESPONSE_FORMAT,
    ) -> None:
        self._config = _base.resolve_config(api_key, rapidapi_key, base_url)
        self.response_format = _base.check_response_format(response_format)
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

    def _get(
        self,
        path: str,
        params: Optional[Mapping[str, Optional[QueryValue]]] = None,
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Sends a GET request with retries and returns the parsed JSON body."""
        args = self._request_args(path, params, response_format)
        attempt = 0
        while True:
            try:
                response = self._http.get(timeout=self.timeout, **args)
            except httpx.TimeoutException as exc:
                if attempt < self.max_retries:
                    self._sleep(_base.retry_delay(attempt))
                    attempt += 1
                    continue
                raise APITimeoutError(f"Request to TwittrAPI timed out: {exc}") from exc
            except httpx.TransportError as exc:
                if attempt < self.max_retries:
                    self._sleep(_base.retry_delay(attempt))
                    attempt += 1
                    continue
                raise APIConnectionError(f"Could not reach TwittrAPI: {exc}") from exc

            if attempt < self.max_retries and _base.should_retry_status(response.status_code):
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

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        rapidapi_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: TimeoutTypes = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: Optional[httpx.AsyncClient] = None,
        response_format: ResponseFormat = DEFAULT_RESPONSE_FORMAT,
    ) -> None:
        self._config = _base.resolve_config(api_key, rapidapi_key, base_url)
        self.response_format = _base.check_response_format(response_format)
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

    async def _get(
        self,
        path: str,
        params: Optional[Mapping[str, Optional[QueryValue]]] = None,
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        args = self._request_args(path, params, response_format)
        attempt = 0
        while True:
            try:
                response = await self._http.get(timeout=self.timeout, **args)
            except httpx.TimeoutException as exc:
                if attempt < self.max_retries:
                    await self._sleep(_base.retry_delay(attempt))
                    attempt += 1
                    continue
                raise APITimeoutError(f"Request to TwittrAPI timed out: {exc}") from exc
            except httpx.TransportError as exc:
                if attempt < self.max_retries:
                    await self._sleep(_base.retry_delay(attempt))
                    attempt += 1
                    continue
                raise APIConnectionError(f"Could not reach TwittrAPI: {exc}") from exc

            if attempt < self.max_retries and _base.should_retry_status(response.status_code):
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
