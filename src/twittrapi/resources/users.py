from __future__ import annotations

from typing import Any, Iterable, Optional

from .. import _endpoints as E
from .._endpoints import ID
from ._base import AsyncResource, SyncResource

__all__ = ["Users", "AsyncUsers"]


class Users(SyncResource):
    """Profiles and user timelines.

    Timeline methods (``tweets``, ``followers``, ...) take either ``user_id`` or ``username``.
    The ID is slightly faster; with only a username the API resolves it for you.
    """

    def get_by_username(self, username: str) -> Any:
        """Profile by handle (a leading ``@`` is fine). Includes the numeric ``rest_id``."""
        return self._get(E.user_by_username(username))

    def get_by_id(self, user_id: ID) -> Any:
        """Profile by numeric user ID."""
        return self._get(E.user_by_id(user_id))

    def username_to_id(self, username: str) -> Any:
        """Resolve a handle to its numeric user ID. Smaller and cheaper than ``get_by_username``."""
        return self._get(E.username_to_id(username))

    def get_many(self, user_ids: Iterable[ID]) -> Any:
        """Profiles for up to 100 users by numeric ID, in one call."""
        return self._get(E.users_by_ids(user_ids))

    def tweets(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """A user's tweets, newest first, without replies. Paginated."""
        return self._get(E.user_timeline("tweets", user_id, username, count, cursor))

    def tweets_and_replies(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """A user's tweets including replies, newest first. Paginated."""
        return self._get(E.user_timeline("tweets_and_replies", user_id, username, count, cursor))

    def media(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """A user's tweets that contain photos or videos. Paginated."""
        return self._get(E.user_timeline("media", user_id, username, count, cursor))

    def followers(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """Accounts that follow a user, newest first. Paginated."""
        return self._get(E.user_timeline("followers", user_id, username, count, cursor))

    def following(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """Accounts a user follows. Paginated."""
        return self._get(E.user_timeline("following", user_id, username, count, cursor))

    def verified_followers(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """A user's followers that have a verified badge. Paginated."""
        return self._get(E.user_timeline("verified_followers", user_id, username, count, cursor))


class AsyncUsers(AsyncResource):
    """Async version of :class:`Users`."""

    async def get_by_username(self, username: str) -> Any:
        """Profile by handle (a leading ``@`` is fine). Includes the numeric ``rest_id``."""
        return await self._get(E.user_by_username(username))

    async def get_by_id(self, user_id: ID) -> Any:
        """Profile by numeric user ID."""
        return await self._get(E.user_by_id(user_id))

    async def username_to_id(self, username: str) -> Any:
        """Resolve a handle to its numeric user ID. Smaller and cheaper than ``get_by_username``."""
        return await self._get(E.username_to_id(username))

    async def get_many(self, user_ids: Iterable[ID]) -> Any:
        """Profiles for up to 100 users by numeric ID, in one call."""
        return await self._get(E.users_by_ids(user_ids))

    async def tweets(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """A user's tweets, newest first, without replies. Paginated."""
        return await self._get(E.user_timeline("tweets", user_id, username, count, cursor))

    async def tweets_and_replies(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """A user's tweets including replies, newest first. Paginated."""
        return await self._get(E.user_timeline("tweets_and_replies", user_id, username, count, cursor))

    async def media(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """A user's tweets that contain photos or videos. Paginated."""
        return await self._get(E.user_timeline("media", user_id, username, count, cursor))

    async def followers(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """Accounts that follow a user, newest first. Paginated."""
        return await self._get(E.user_timeline("followers", user_id, username, count, cursor))

    async def following(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """Accounts a user follows. Paginated."""
        return await self._get(E.user_timeline("following", user_id, username, count, cursor))

    async def verified_followers(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """A user's followers that have a verified badge. Paginated."""
        return await self._get(E.user_timeline("verified_followers", user_id, username, count, cursor))
