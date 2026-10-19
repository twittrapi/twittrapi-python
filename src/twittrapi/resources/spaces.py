from __future__ import annotations

from typing import Any, Optional

from .. import _endpoints as E
from .._base import ResponseFormat
from ._base import AsyncResource, SyncResource

__all__ = ["Spaces", "AsyncSpaces"]


class Spaces(SyncResource):
    """X Spaces (live audio)."""

    def get(
        self,
        space_id: str,
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """A Space: title, state, host and participants, and whether a replay is available.

        ``space_id`` is the ID from the Space's link (``x.com/i/spaces/<id>``, e.g.
        ``"1YqKDqWqdPLsV"``): letters and digits. Raw format only.
        """
        return self._get(E.space(space_id), response_format)


class AsyncSpaces(AsyncResource):
    """Async version of :class:`Spaces`."""

    async def get(
        self,
        space_id: str,
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """A Space: title, state, host and participants, and whether a replay is available.

        ``space_id`` is the ID from the Space's link (``x.com/i/spaces/<id>``, e.g.
        ``"1YqKDqWqdPLsV"``): letters and digits. Raw format only.
        """
        return await self._get(E.space(space_id), response_format)
