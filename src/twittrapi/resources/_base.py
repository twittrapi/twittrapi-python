from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .._base import ResponseFormat
from .._endpoints import EndpointRequest

if TYPE_CHECKING:
    from .._client import AsyncTwittrAPI, TwittrAPI


class SyncResource:
    def __init__(self, client: "TwittrAPI") -> None:
        self._client = client

    def _get(
        self, request: EndpointRequest, response_format: Optional[ResponseFormat] = None
    ) -> Any:
        return self._client._get(request.path, request.params, response_format=response_format)

    def _post(
        self, request: EndpointRequest, response_format: Optional[ResponseFormat] = None
    ) -> Any:
        return self._client._post(
            request.path, request.params, request.body, response_format=response_format
        )


class AsyncResource:
    def __init__(self, client: "AsyncTwittrAPI") -> None:
        self._client = client

    async def _get(
        self, request: EndpointRequest, response_format: Optional[ResponseFormat] = None
    ) -> Any:
        return await self._client._get(
            request.path, request.params, response_format=response_format
        )

    async def _post(
        self, request: EndpointRequest, response_format: Optional[ResponseFormat] = None
    ) -> Any:
        return await self._client._post(
            request.path, request.params, request.body, response_format=response_format
        )
