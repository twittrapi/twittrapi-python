from __future__ import annotations

from typing import Any, Optional

from .. import _endpoints as E
from ._base import AsyncResource, SyncResource

__all__ = ["Search", "AsyncSearch"]


class Search(SyncResource):
    """Search, same as the X search box."""

    def tweets(
        self,
        query: str,
        *,
        category: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """Search tweets. ``query`` supports X search operators (``from:``, ``lang:``,
        ``since:``, ``min_faves:``, ``-filter:replies`` ...).

        ``category`` is one of "Top" (default), "Latest", "People", "Photos", "Videos".
        "People" returns accounts instead of tweets. Paginated.
        """
        return self._get(E.search_tweets(query, category, count, cursor))


class AsyncSearch(AsyncResource):
    """Async version of :class:`Search`."""

    async def tweets(
        self,
        query: str,
        *,
        category: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """Search tweets. ``query`` supports X search operators (``from:``, ``lang:``,
        ``since:``, ``min_faves:``, ``-filter:replies`` ...).

        ``category`` is one of "Top" (default), "Latest", "People", "Photos", "Videos".
        "People" returns accounts instead of tweets. Paginated.
        """
        return await self._get(E.search_tweets(query, category, count, cursor))
