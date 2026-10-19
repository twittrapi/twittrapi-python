from __future__ import annotations

from typing import Any, Optional

from .. import _endpoints as E
from .._base import ResponseFormat
from .._endpoints import ID
from ._base import AsyncResource, SyncResource

__all__ = ["Communities", "AsyncCommunities"]


class Communities(SyncResource):
    """X Communities."""

    def get(
        self,
        community_id: ID,
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Name, description, rules, member count and admins."""
        return self._get(E.community(community_id), response_format)

    def about(
        self,
        community_id: ID,
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """The community's About page: description, rules, creation date, moderators and a
        preview of its members. Raw format only."""
        return self._get(E.community_about(community_id), response_format)

    def tweets(
        self,
        community_id: ID,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Tweets posted in the community. Paginated."""
        return self._get(E.community_tweets(community_id, count, cursor), response_format)

    def search(
        self,
        query: str,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Find communities by keyword. Paginated."""
        return self._get(E.community_search(query, count, cursor), response_format)


class AsyncCommunities(AsyncResource):
    """Async version of :class:`Communities`."""

    async def get(
        self,
        community_id: ID,
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Name, description, rules, member count and admins."""
        return await self._get(E.community(community_id), response_format)

    async def about(
        self,
        community_id: ID,
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """The community's About page: description, rules, creation date, moderators and a
        preview of its members. Raw format only."""
        return await self._get(E.community_about(community_id), response_format)

    async def tweets(
        self,
        community_id: ID,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Tweets posted in the community. Paginated."""
        return await self._get(E.community_tweets(community_id, count, cursor), response_format)

    async def search(
        self,
        query: str,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Find communities by keyword. Paginated."""
        return await self._get(E.community_search(query, count, cursor), response_format)
