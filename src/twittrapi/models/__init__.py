"""Typed models for the simple response format.

Resource methods return parsed JSON (dicts and lists). With ``response_format="simple"`` that
JSON has a small, fixed schema (https://twittrapi.com/docs/simple-format), and these
dataclasses give it types::

    from twittrapi import TwittrAPI
    from twittrapi.models import User, tweets_page

    client = TwittrAPI(response_format="simple")
    page = tweets_page(client.users.tweets(username="XDevelopers"))
    for tweet in page.data:
        print(tweet.id, tweet.text)
    if page.has_next_page:
        more = client.users.tweets(username="XDevelopers", cursor=page.next_cursor)

    user = User.from_dict(client.users.get_by_username("XDevelopers")["data"])

Attribute names are the snake_case versions of the JSON fields (``nextCursor`` becomes
``next_cursor``, ``hasNextPage`` becomes ``has_next_page``). Parsing is lenient: a missing
field gets its documented empty value (``None``, ``""``, ``0``, ``False`` or ``[]``) and
fields added to the API later are ignored. These models do not apply to the raw format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Generic, List, Mapping, Optional, TypeVar, Union

__all__ = [
    "Article",
    "Media",
    "Page",
    "ReplyTo",
    "Tweet",
    "TweetCounts",
    "UnavailableTweet",
    "User",
    "UserCounts",
    "UserRef",
    "parse_tweet",
    "tweets_page",
    "users_page",
]

T = TypeVar("T")


def _obj(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _str(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _opt_str(value: Any) -> Optional[str]:
    return value if isinstance(value, str) else None


def _int(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _opt_int(value: Any) -> Optional[int]:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _bool(value: Any) -> bool:
    return value is True


def _str_list(value: Any) -> List[str]:
    return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []


def _list(value: Any) -> List[Mapping[str, Any]]:
    return [v for v in value if isinstance(v, Mapping)] if isinstance(value, list) else []


@dataclass(frozen=True)
class UserRef:
    """A short reference to an account: ``{id, username}``."""

    id: str
    username: str

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> UserRef:
        return cls(id=_str(data.get("id")), username=_str(data.get("username")))


@dataclass(frozen=True)
class UserCounts:
    followers: int = 0
    following: int = 0
    tweets: int = 0
    likes: int = 0
    media: int = 0
    listed: int = 0

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> UserCounts:
        return cls(
            followers=_int(data.get("followers")),
            following=_int(data.get("following")),
            tweets=_int(data.get("tweets")),
            likes=_int(data.get("likes")),
            media=_int(data.get("media")),
            listed=_int(data.get("listed")),
        )


@dataclass(frozen=True)
class User:
    """An account in the simple format."""

    id: str
    username: str
    name: str = ""
    description: str = ""
    location: str = ""
    url: Optional[str] = None
    created_at: Optional[str] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    verified: bool = False
    verified_type: Optional[str] = None
    protected: bool = False
    counts: UserCounts = field(default_factory=UserCounts)
    pinned_tweet_ids: List[str] = field(default_factory=list)
    is_automated: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> User:
        return cls(
            id=_str(data.get("id")),
            username=_str(data.get("username")),
            name=_str(data.get("name")),
            description=_str(data.get("description")),
            location=_str(data.get("location")),
            url=_opt_str(data.get("url")),
            created_at=_opt_str(data.get("createdAt")),
            avatar_url=_opt_str(data.get("avatarUrl")),
            banner_url=_opt_str(data.get("bannerUrl")),
            verified=_bool(data.get("verified")),
            verified_type=_opt_str(data.get("verifiedType")),
            protected=_bool(data.get("protected")),
            counts=UserCounts.from_dict(_obj(data.get("counts"))),
            pinned_tweet_ids=_str_list(data.get("pinnedTweetIds")),
            is_automated=_bool(data.get("isAutomated")),
        )


@dataclass(frozen=True)
class TweetCounts:
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    quotes: int = 0
    bookmarks: int = 0
    views: Optional[int] = None  # None when X hides the view count

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> TweetCounts:
        return cls(
            likes=_int(data.get("likes")),
            retweets=_int(data.get("retweets")),
            replies=_int(data.get("replies")),
            quotes=_int(data.get("quotes")),
            bookmarks=_int(data.get("bookmarks")),
            views=_opt_int(data.get("views")),
        )


@dataclass(frozen=True)
class Media:
    """A photo, video or GIF. For videos and GIFs ``url`` is the highest-bitrate MP4 and
    ``preview_url`` the poster image."""

    type: str
    url: str
    preview_url: str = ""
    width: int = 0
    height: int = 0
    alt_text: Optional[str] = None
    duration_ms: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Media:
        return cls(
            type=_str(data.get("type")),
            url=_str(data.get("url")),
            preview_url=_str(data.get("previewUrl")),
            width=_int(data.get("width")),
            height=_int(data.get("height")),
            alt_text=_opt_str(data.get("altText")),
            duration_ms=_opt_int(data.get("durationMs")),
        )


@dataclass(frozen=True)
class ReplyTo:
    """The tweet (and its author) a reply answers."""

    tweet_id: Optional[str] = None
    user_id: Optional[str] = None
    username: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ReplyTo:
        return cls(
            tweet_id=_opt_str(data.get("tweetId")),
            user_id=_opt_str(data.get("userId")),
            username=_opt_str(data.get("username")),
        )


@dataclass(frozen=True)
class Article:
    """A long-form X Article attached to a tweet."""

    id: str
    title: str = ""
    preview_text: str = ""
    cover_image_url: Optional[str] = None
    published_at: Optional[str] = None
    text: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Article:
        return cls(
            id=_str(data.get("id")),
            title=_str(data.get("title")),
            preview_text=_str(data.get("previewText")),
            cover_image_url=_opt_str(data.get("coverImageUrl")),
            published_at=_opt_str(data.get("publishedAt")),
            text=_opt_str(data.get("text")),
        )


@dataclass(frozen=True)
class UnavailableTweet:
    """Stands in for a tweet X did not return (deleted, withheld, protected) whose ID is
    known: ``{"id": "...", "unavailable": true}``."""

    id: str
    unavailable: bool = True


@dataclass(frozen=True)
class Tweet:
    """A post in the simple format."""

    id: str
    url: str = ""
    text: str = ""
    created_at: Optional[str] = None
    lang: Optional[str] = None
    author: Optional[User] = None
    counts: TweetCounts = field(default_factory=TweetCounts)
    media: List[Media] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    mentions: List[UserRef] = field(default_factory=list)
    reply_to: Optional[ReplyTo] = None
    quoted: Optional[Union[Tweet, UnavailableTweet]] = None
    retweet_of: Optional[Union[Tweet, UnavailableTweet]] = None
    conversation_id: Optional[str] = None
    is_pinned: bool = False
    source: Optional[str] = None
    article: Optional[Article] = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Tweet:
        author = data.get("author")
        reply_to = data.get("replyTo")
        quoted = data.get("quoted")
        retweet_of = data.get("retweetOf")
        article = data.get("article")
        return cls(
            id=_str(data.get("id")),
            url=_str(data.get("url")),
            text=_str(data.get("text")),
            created_at=_opt_str(data.get("createdAt")),
            lang=_opt_str(data.get("lang")),
            author=User.from_dict(author) if isinstance(author, Mapping) else None,
            counts=TweetCounts.from_dict(_obj(data.get("counts"))),
            media=[Media.from_dict(m) for m in _list(data.get("media"))],
            urls=_str_list(data.get("urls")),
            hashtags=_str_list(data.get("hashtags")),
            mentions=[UserRef.from_dict(m) for m in _list(data.get("mentions"))],
            reply_to=ReplyTo.from_dict(reply_to) if isinstance(reply_to, Mapping) else None,
            quoted=parse_tweet(quoted) if isinstance(quoted, Mapping) else None,
            retweet_of=parse_tweet(retweet_of) if isinstance(retweet_of, Mapping) else None,
            conversation_id=_opt_str(data.get("conversationId")),
            is_pinned=_bool(data.get("isPinned")),
            source=_opt_str(data.get("source")),
            article=Article.from_dict(article) if isinstance(article, Mapping) else None,
        )


def parse_tweet(data: Mapping[str, Any]) -> Union[Tweet, UnavailableTweet]:
    """Parses one item of a tweet list: a :class:`Tweet`, or an :class:`UnavailableTweet`
    for the ``{"id": ..., "unavailable": true}`` placeholder."""
    if data.get("unavailable") is True:
        return UnavailableTweet(id=_str(data.get("id")))
    return Tweet.from_dict(data)


@dataclass(frozen=True)
class Page(Generic[T]):
    """A list response in the simple format.

    ``next_cursor`` is ``None`` and ``has_next_page`` is ``False`` on the last page; pass
    ``next_cursor`` as ``cursor`` to get the next one. ``previous_cursor`` is X's top cursor
    (use it to poll for newer items).
    """

    data: List[T]
    next_cursor: Optional[str] = None
    previous_cursor: Optional[str] = None
    has_next_page: bool = False

    @classmethod
    def from_dict(
        cls, body: Mapping[str, Any], item: Callable[[Mapping[str, Any]], T]
    ) -> Page[T]:
        """Parses ``{"data": [...], "nextCursor", "previousCursor", "hasNextPage"}``, turning
        each item of ``data`` into a model with ``item`` (e.g. :meth:`User.from_dict`)."""
        if not isinstance(body, Mapping) or not isinstance(body.get("data"), list):
            raise TypeError(
                "Expected a simple-format list response ({'data': [...], 'nextCursor': ...}). "
                "Was the request sent with response_format='simple'?"
            )
        next_cursor = _opt_str(body.get("nextCursor")) or None
        has_next = _bool(body.get("hasNextPage")) and next_cursor is not None
        return cls(
            data=[item(d) for d in _list(body.get("data"))],
            next_cursor=next_cursor if has_next else None,
            previous_cursor=_opt_str(body.get("previousCursor")),
            has_next_page=has_next,
        )


def tweets_page(body: Mapping[str, Any]) -> Page[Union[Tweet, UnavailableTweet]]:
    """Parses a simple-format tweet list (timelines, search, quotes, list and community
    tweets, a tweet with its replies, ``tweets.replies``, ``tweets.thread``,
    ``tweets.get_many``)."""
    return Page.from_dict(body, parse_tweet)


def users_page(body: Mapping[str, Any]) -> Page[User]:
    """Parses a simple-format user list (followers, following, likers, retweeters, list
    members, ``users.affiliates``, ``users.get_many``, search with ``category="People"``)."""
    return Page.from_dict(body, User.from_dict)
