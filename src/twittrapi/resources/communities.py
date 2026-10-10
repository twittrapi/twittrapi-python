from __future__ import annotations

from typing import Any, Optional

from .. import _endpoints as E
from .._endpoints import ID
from ._base import AsyncResource, SyncResource

__all__ = ["Communities", "AsyncCommunities"]


class Communities(SyncResource):
    """X Communities."""

    def get(self, community_id: ID) -> Any:
        """Name, description, rules, member count and admins."""
        return self._get(E.community(community_id))

    def tweets(
        self, community_id: ID, *, count: Optional[int] = None, cursor: Optional[str] = None
    ) -> Any:
        """Tweets posted in the community. Paginated."""
        return self._get(E.community_tweets(community_id, count, cursor))

    def search(
        self, query: str, *, count: Optional[int] = None, cursor: Optional[str] = None
    ) -> Any:
        """Find communities by keyword. Paginated."""
        return self._get(E.community_search(query, count, cursor))


class AsyncCommunities(AsyncResource):
    """Async version of :class:`Communities`."""

    async def get(self, community_id: ID) -> Any:
        """Name, description, rules, member count and admins."""
        return await self._get(E.community(community_id))

    async def tweets(
        self, community_id: ID, *, count: Optional[int] = None, cursor: Optional[str] = None
    ) -> Any:
        """Tweets posted in the community. Paginated."""
        return await self._get(E.community_tweets(community_id, count, cursor))

    async def search(
        self, query: str, *, count: Optional[int] = None, cursor: Optional[str] = None
    ) -> Any:
        """Find communities by keyword. Paginated."""
        return await self._get(E.community_search(query, count, cursor))
