from __future__ import annotations

from typing import Any, Iterable, Optional

from .. import _endpoints as E
from .._base import ResponseFormat
from .._endpoints import ID
from ._base import AsyncResource, SyncResource

__all__ = ["Users", "AsyncUsers"]


class Users(SyncResource):
    """Profiles and user timelines.

    Timeline methods (``tweets``, ``followers``, ...) take either ``user_id`` or ``username``.
    The ID is slightly faster; with only a username the API resolves it for you.
    """

    def get_by_username(
        self,
        username: str,
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Profile by handle (a leading ``@`` is fine). Includes the numeric ``rest_id``."""
        return self._get(E.user_by_username(username), response_format)

    def get_by_id(
        self,
        user_id: ID,
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Profile by numeric user ID."""
        return self._get(E.user_by_id(user_id), response_format)

    def username_to_id(
        self,
        username: str,
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Resolve a handle to its numeric user ID. Smaller and cheaper than ``get_by_username``."""
        return self._get(E.username_to_id(username), response_format)

    def get_many(
        self,
        user_ids: Iterable[ID],
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Profiles for up to 500 users by numeric ID, in one call."""
        return self._get(E.users_by_ids(user_ids), response_format)

    def tweets(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """A user's tweets, newest first, without replies. Paginated."""
        request = E.user_timeline("tweets", user_id, username, count, cursor)
        return self._get(request, response_format)

    def tweets_and_replies(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """A user's tweets including replies, newest first. Paginated."""
        request = E.user_timeline("tweets_and_replies", user_id, username, count, cursor)
        return self._get(request, response_format)

    def media(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """A user's tweets that contain photos or videos. Paginated."""
        request = E.user_timeline("media", user_id, username, count, cursor)
        return self._get(request, response_format)

    def followers(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Accounts that follow a user, newest first. Paginated."""
        request = E.user_timeline("followers", user_id, username, count, cursor)
        return self._get(request, response_format)

    def following(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Accounts a user follows. Paginated."""
        request = E.user_timeline("following", user_id, username, count, cursor)
        return self._get(request, response_format)

    def verified_followers(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """A user's followers that have a verified badge. Paginated."""
        request = E.user_timeline("verified_followers", user_id, username, count, cursor)
        return self._get(request, response_format)

    def affiliates(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Accounts affiliated with an organization (the affiliates shown on its profile).
        Paginated. In the simple format a list of users, like :meth:`followers`."""
        request = E.user_timeline("affiliates", user_id, username, count, cursor)
        return self._get(request, response_format)

    def friendships_batch(
        self,
        source: str,
        targets: Iterable[str],
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """How the account ``source`` relates to up to 50 others (following, followed by,
        blocking, muting, ...), in one request.

        ``targets`` is a list of handles (``@`` optional); duplicates are dropped
        (case-insensitive). Billed one call per distinct target. Answers
        ``{"source_screen_name", "relationships": [{"target_screen_name", "relationship"}],
        "errors"}`` in input order; ``errors`` lists the handles that failed and is left out
        when none did. Raw format only.
        """
        return self._get(E.friendships_batch(source, targets), response_format)

    def about_batch(
        self,
        usernames: Iterable[str],
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """The "About this account" details (where the account is based, username changes,
        ...) for up to 20 handles, in one request.

        ``@`` is optional and duplicates are dropped (case-insensitive). Billed one call per
        distinct handle. Answers ``{"users": [{"username", "about"}], "errors"}``; ``errors``
        lists the handles that were not found or failed and is left out when none did. Raw
        format only.
        """
        return self._get(E.about_batch(usernames), response_format)


class AsyncUsers(AsyncResource):
    """Async version of :class:`Users`."""

    async def get_by_username(
        self,
        username: str,
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Profile by handle (a leading ``@`` is fine). Includes the numeric ``rest_id``."""
        return await self._get(E.user_by_username(username), response_format)

    async def get_by_id(
        self,
        user_id: ID,
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Profile by numeric user ID."""
        return await self._get(E.user_by_id(user_id), response_format)

    async def username_to_id(
        self,
        username: str,
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Resolve a handle to its numeric user ID. Smaller and cheaper than ``get_by_username``."""
        return await self._get(E.username_to_id(username), response_format)

    async def get_many(
        self,
        user_ids: Iterable[ID],
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Profiles for up to 500 users by numeric ID, in one call."""
        return await self._get(E.users_by_ids(user_ids), response_format)

    async def tweets(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """A user's tweets, newest first, without replies. Paginated."""
        request = E.user_timeline("tweets", user_id, username, count, cursor)
        return await self._get(request, response_format)

    async def tweets_and_replies(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """A user's tweets including replies, newest first. Paginated."""
        request = E.user_timeline("tweets_and_replies", user_id, username, count, cursor)
        return await self._get(request, response_format)

    async def media(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """A user's tweets that contain photos or videos. Paginated."""
        request = E.user_timeline("media", user_id, username, count, cursor)
        return await self._get(request, response_format)

    async def followers(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Accounts that follow a user, newest first. Paginated."""
        request = E.user_timeline("followers", user_id, username, count, cursor)
        return await self._get(request, response_format)

    async def following(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Accounts a user follows. Paginated."""
        request = E.user_timeline("following", user_id, username, count, cursor)
        return await self._get(request, response_format)

    async def verified_followers(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """A user's followers that have a verified badge. Paginated."""
        request = E.user_timeline("verified_followers", user_id, username, count, cursor)
        return await self._get(request, response_format)

    async def affiliates(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Accounts affiliated with an organization (the affiliates shown on its profile).
        Paginated. In the simple format a list of users, like :meth:`followers`."""
        request = E.user_timeline("affiliates", user_id, username, count, cursor)
        return await self._get(request, response_format)

    async def friendships_batch(
        self,
        source: str,
        targets: Iterable[str],
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """How the account ``source`` relates to up to 50 others (following, followed by,
        blocking, muting, ...), in one request.

        ``targets`` is a list of handles (``@`` optional); duplicates are dropped
        (case-insensitive). Billed one call per distinct target. Answers
        ``{"source_screen_name", "relationships": [{"target_screen_name", "relationship"}],
        "errors"}`` in input order; ``errors`` lists the handles that failed and is left out
        when none did. Raw format only.
        """
        return await self._get(E.friendships_batch(source, targets), response_format)

    async def about_batch(
        self,
        usernames: Iterable[str],
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """The "About this account" details (where the account is based, username changes,
        ...) for up to 20 handles, in one request.

        ``@`` is optional and duplicates are dropped (case-insensitive). Billed one call per
        distinct handle. Answers ``{"users": [{"username", "about"}], "errors"}``; ``errors``
        lists the handles that were not found or failed and is left out when none did. Raw
        format only.
        """
        return await self._get(E.about_batch(usernames), response_format)
