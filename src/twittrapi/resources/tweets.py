from __future__ import annotations

from typing import Any, Iterable, Optional

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

    def get_many(
        self,
        tweet_ids: Iterable[ID],
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Up to 100 tweets by numeric ID, in one call (billed as one call).

        Raw format: one entry per ID in request order, ``{}`` for an ID without a tweet
        (deleted or never existed). Simple format: a list of the tweets found, in request
        order; IDs without a tweet are left out.
        """
        return self._get(E.tweets_by_ids(tweet_ids), response_format)

    def replies(
        self,
        tweet_id: ID,
        *,
        ranking_mode: Optional[str] = None,
        include_promoted_content: Optional[bool] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Only the replies to a tweet, without the tweet itself. Paginated.

        ``ranking_mode`` orders them: "Relevance" (default), "Recency" or "Likes". In the
        simple format a list of tweets in display order.
        """
        return self._get(
            E.tweet_replies(tweet_id, ranking_mode, include_promoted_content, cursor),
            response_format,
        )

    def thread(
        self,
        tweet_id: ID,
        *,
        ranking_mode: Optional[str] = None,
        include_promoted_content: Optional[bool] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """The author's thread around a tweet: their tweets above it and their own replies
        below it, up to the first reply by someone else.

        Not paginated: long threads are loaded in full, as one billed call. In the simple
        format a list of tweets in reading order.
        """
        return self._get(
            E.tweet_thread(tweet_id, ranking_mode, include_promoted_content), response_format
        )

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

    async def get_many(
        self,
        tweet_ids: Iterable[ID],
        *,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Up to 100 tweets by numeric ID, in one call (billed as one call).

        Raw format: one entry per ID in request order, ``{}`` for an ID without a tweet
        (deleted or never existed). Simple format: a list of the tweets found, in request
        order; IDs without a tweet are left out.
        """
        return await self._get(E.tweets_by_ids(tweet_ids), response_format)

    async def replies(
        self,
        tweet_id: ID,
        *,
        ranking_mode: Optional[str] = None,
        include_promoted_content: Optional[bool] = None,
        cursor: Optional[str] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Only the replies to a tweet, without the tweet itself. Paginated.

        ``ranking_mode`` orders them: "Relevance" (default), "Recency" or "Likes". In the
        simple format a list of tweets in display order.
        """
        return await self._get(
            E.tweet_replies(tweet_id, ranking_mode, include_promoted_content, cursor),
            response_format,
        )

    async def thread(
        self,
        tweet_id: ID,
        *,
        ranking_mode: Optional[str] = None,
        include_promoted_content: Optional[bool] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """The author's thread around a tweet: their tweets above it and their own replies
        below it, up to the first reply by someone else.

        Not paginated: long threads are loaded in full, as one billed call. In the simple
        format a list of tweets in reading order.
        """
        return await self._get(
            E.tweet_thread(tweet_id, ranking_mode, include_promoted_content), response_format
        )

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
