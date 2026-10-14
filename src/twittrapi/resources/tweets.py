from __future__ import annotations

from typing import Any, Optional

from .. import _endpoints as E
from .._base import ResponseFormat
from .._endpoints import ID
from ._base import AsyncResource, SyncResource

__all__ = ["Tweets", "AsyncTweets"]


class Tweets(SyncResource):
    """Single tweets and the users and tweets around them."""

    def get(
        self,
        tweet_id: ID,
        *,
        ranking_mode: Optional[str] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """A tweet with its author, media, counts and reply thread.

        ``ranking_mode`` orders the replies: "Relevance" (default), "Recency" or "Likes".
        Pass ``cursor`` to load more replies.
        """
        return self._get(E.tweet(tweet_id, ranking_mode, cursor), response_format)

    def retweeters(
        self,
        tweet_id: ID,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Users who retweeted a tweet. Paginated."""
        return self._get(E.tweet_retweeters(tweet_id, count, cursor), response_format)

    def likers(
        self,
        tweet_id: ID,
        *,
        cookie: str,
        proxy: str,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Users who liked a tweet. Paginated.

        Works only for your own tweets: X shows likers only to the author. ``cookie`` is the
        Cookie header of the account that posted the tweet (with ``auth_token`` and ``ct0``),
        ``proxy`` is ``http://user:pass@host:port``. Both, and the paging, are sent as a POST
        body. For anyone else's tweet the list is empty.
        """
        return self._post(
            E.tweet_likers(tweet_id, cookie, proxy, count, cursor), response_format
        )

    def quotes(
        self,
        tweet_id: ID,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Tweets that quote a tweet. Paginated."""
        return self._get(E.tweet_quotes(tweet_id, count, cursor), response_format)


class AsyncTweets(AsyncResource):
    """Async version of :class:`Tweets`."""

    async def get(
        self,
        tweet_id: ID,
        *,
        ranking_mode: Optional[str] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """A tweet with its author, media, counts and reply thread.

        ``ranking_mode`` orders the replies: "Relevance" (default), "Recency" or "Likes".
        Pass ``cursor`` to load more replies.
        """
        return await self._get(E.tweet(tweet_id, ranking_mode, cursor), response_format)

    async def retweeters(
        self,
        tweet_id: ID,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Users who retweeted a tweet. Paginated."""
        return await self._get(E.tweet_retweeters(tweet_id, count, cursor), response_format)

    async def likers(
        self,
        tweet_id: ID,
        *,
        cookie: str,
        proxy: str,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Users who liked a tweet. Paginated.

        Works only for your own tweets: X shows likers only to the author. ``cookie`` is the
        Cookie header of the account that posted the tweet (with ``auth_token`` and ``ct0``),
        ``proxy`` is ``http://user:pass@host:port``. Both, and the paging, are sent as a POST
        body. For anyone else's tweet the list is empty.
        """
        return await self._post(
            E.tweet_likers(tweet_id, cookie, proxy, count, cursor), response_format
        )

    async def quotes(
        self,
        tweet_id: ID,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Tweets that quote a tweet. Paginated."""
        return await self._get(E.tweet_quotes(tweet_id, count, cursor), response_format)
