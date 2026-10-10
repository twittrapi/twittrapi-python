from __future__ import annotations

from typing import Any, Optional

from .. import _endpoints as E
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
    ) -> Any:
        """A tweet with its author, media, counts and reply thread.

        ``ranking_mode`` orders the replies: "Relevance" (default), "Recency" or "Likes".
        Pass ``cursor`` to load more replies.
        """
        return self._get(E.tweet(tweet_id, ranking_mode, cursor))

    def retweeters(
        self, tweet_id: ID, *, count: Optional[int] = None, cursor: Optional[str] = None
    ) -> Any:
        """Users who retweeted a tweet. Paginated."""
        return self._get(E.tweet_retweeters(tweet_id, count, cursor))

    def likers(
        self, tweet_id: ID, *, count: Optional[int] = None, cursor: Optional[str] = None
    ) -> Any:
        """Users who liked a tweet. X hides likers for many tweets, so this can be empty."""
        return self._get(E.tweet_likers(tweet_id, count, cursor))

    def quotes(
        self, tweet_id: ID, *, count: Optional[int] = None, cursor: Optional[str] = None
    ) -> Any:
        """Tweets that quote a tweet. Paginated."""
        return self._get(E.tweet_quotes(tweet_id, count, cursor))


class AsyncTweets(AsyncResource):
    """Async version of :class:`Tweets`."""

    async def get(
        self,
        tweet_id: ID,
        *,
        ranking_mode: Optional[str] = None,
        cursor: Optional[str] = None,
    ) -> Any:
        """A tweet with its author, media, counts and reply thread.

        ``ranking_mode`` orders the replies: "Relevance" (default), "Recency" or "Likes".
        Pass ``cursor`` to load more replies.
        """
        return await self._get(E.tweet(tweet_id, ranking_mode, cursor))

    async def retweeters(
        self, tweet_id: ID, *, count: Optional[int] = None, cursor: Optional[str] = None
    ) -> Any:
        """Users who retweeted a tweet. Paginated."""
        return await self._get(E.tweet_retweeters(tweet_id, count, cursor))

    async def likers(
        self, tweet_id: ID, *, count: Optional[int] = None, cursor: Optional[str] = None
    ) -> Any:
        """Users who liked a tweet. X hides likers for many tweets, so this can be empty."""
        return await self._get(E.tweet_likers(tweet_id, count, cursor))

    async def quotes(
        self, tweet_id: ID, *, count: Optional[int] = None, cursor: Optional[str] = None
    ) -> Any:
        """Tweets that quote a tweet. Paginated."""
        return await self._get(E.tweet_quotes(tweet_id, count, cursor))
