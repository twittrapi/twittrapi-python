from __future__ import annotations

from typing import Any, Optional

from .. import _endpoints as E
from .._base import ResponseFormat
from .._endpoints import ID
from ._base import AsyncResource, SyncResource

__all__ = ["Lists", "AsyncLists"]


class Lists(SyncResource):
    """X lists, by numeric list ID (the number in the list URL)."""

    def details(
        self,
        list_id: ID,
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Name, description, owner and member/follower counts."""
        return self._get(E.list_details(list_id), response_format)

    def tweets(
        self,
        list_id: ID,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Tweets from the list's members, newest first. Paginated."""
        return self._get(E.list_tweets(list_id, count, cursor), response_format)

    def members(
        self,
        list_id: ID,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Accounts that are members of the list. Paginated."""
        return self._get(E.list_members(list_id, count, cursor), response_format)


class AsyncLists(AsyncResource):
    """Async version of :class:`Lists`."""

    async def details(
        self,
        list_id: ID,
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Name, description, owner and member/follower counts."""
        return await self._get(E.list_details(list_id), response_format)

    async def tweets(
        self,
        list_id: ID,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Tweets from the list's members, newest first. Paginated."""
        return await self._get(E.list_tweets(list_id, count, cursor), response_format)

    async def members(
        self,
        list_id: ID,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Accounts that are members of the list. Paginated."""
        return await self._get(E.list_members(list_id, count, cursor), response_format)
