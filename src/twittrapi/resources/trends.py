from __future__ import annotations

from typing import Any

from .. import _endpoints as E
from .._endpoints import ID
from ._base import AsyncResource, SyncResource

__all__ = ["Trends", "AsyncTrends"]


class Trends(SyncResource):
    """Trending topics by location (Yahoo WOEID)."""

    def get(self, location_id: ID = 1) -> Any:
        """Trends for a WOEID: 1 is worldwide, 23424977 the United States,
        23424975 the United Kingdom. Use :meth:`locations` to find others."""
        return self._get(E.trends(location_id))

    def locations(self) -> Any:
        """Countries and cities that have trends, with their WOEIDs."""
        return self._get(E.trend_locations())


class AsyncTrends(AsyncResource):
    """Async version of :class:`Trends`."""

    async def get(self, location_id: ID = 1) -> Any:
        """Trends for a WOEID: 1 is worldwide, 23424977 the United States,
        23424975 the United Kingdom. Use :meth:`locations` to find others."""
        return await self._get(E.trends(location_id))

    async def locations(self) -> Any:
        """Countries and cities that have trends, with their WOEIDs."""
        return await self._get(E.trend_locations())
