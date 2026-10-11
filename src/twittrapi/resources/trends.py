from __future__ import annotations

from typing import Any, Optional

from .. import _endpoints as E
from .._base import ResponseFormat
from .._endpoints import ID
from ._base import AsyncResource, SyncResource

__all__ = ["Trends", "AsyncTrends"]


class Trends(SyncResource):
    """Trending topics by location (Yahoo WOEID)."""

    def get(
        self,
        location_id: ID = 1,
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Trends for a WOEID: 1 is worldwide, 23424977 the United States,
        23424975 the United Kingdom. Use :meth:`locations` to find others."""
        return self._get(E.trends(location_id), response_format)

    def locations(
        self,
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Countries and cities that have trends, with their WOEIDs."""
        return self._get(E.trend_locations(), response_format)


class AsyncTrends(AsyncResource):
    """Async version of :class:`Trends`."""

    async def get(
        self,
        location_id: ID = 1,
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Trends for a WOEID: 1 is worldwide, 23424977 the United States,
        23424975 the United Kingdom. Use :meth:`locations` to find others."""
        return await self._get(E.trends(location_id), response_format)

    async def locations(
        self,
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Countries and cities that have trends, with their WOEIDs."""
        return await self._get(E.trend_locations(), response_format)
