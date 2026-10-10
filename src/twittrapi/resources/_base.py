from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .._endpoints import EndpointRequest

if TYPE_CHECKING:
    from .._client import AsyncTwittrAPI, TwittrAPI


class SyncResource:
    def __init__(self, client: "TwittrAPI") -> None:
        self._client = client

    def _get(self, request: EndpointRequest) -> Any:
        return self._client._get(request.path, request.params)


class AsyncResource:
    def __init__(self, client: "AsyncTwittrAPI") -> None:
        self._client = client

    async def _get(self, request: EndpointRequest) -> Any:
        return await self._client._get(request.path, request.params)
