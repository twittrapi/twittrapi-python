"""Request builders for every TwittrAPI endpoint.

Each function validates its arguments and returns an :class:`EndpointRequest` (path plus query
parameters). The sync and async resource classes both call these, so the mapping from Python
arguments to the HTTP request lives in one place.

All endpoints are GET requests that return X's raw GraphQL JSON.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional, Union
from urllib.parse import quote

ID = Union[str, int]
QueryValue = Union[str, int]

_NUMERIC = re.compile(r"^\d{1,30}$")
_WOEID = re.compile(r"^\d{1,12}$")

MAX_USERS_PER_LOOKUP = 100
SEARCH_CATEGORIES = ("Top", "Latest", "People", "Photos", "Videos")
RANKING_MODES = ("Relevance", "Recency", "Likes")


@dataclass(frozen=True)
class EndpointRequest:
    path: str
    params: Dict[str, QueryValue] = field(default_factory=dict)


def _seg(value: str) -> str:
    """Percent-encodes a single path segment."""
    return quote(value, safe="")


def _numeric_id(value: ID, name: str) -> str:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a numeric ID, got a bool")
    text = str(value).strip()
    if not _NUMERIC.match(text):
        raise ValueError(f"{name} must be a numeric ID (digits only), got {value!r}")
    return text


def _username(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"username must be a string, got {type(value).__name__}")
    text = value.strip().lstrip("@").strip()
    if not text:
        raise ValueError("username must not be empty")
    return text


def _non_empty(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _paging(count: Optional[int], cursor: Optional[str]) -> Dict[str, QueryValue]:
    params: Dict[str, QueryValue] = {}
    if count is not None:
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            raise ValueError(f"count must be a positive integer, got {count!r}")
        params["count"] = count
    if cursor:
        params["cursor"] = cursor
    return params


def _choice(value: Optional[str], name: str, choices: Iterable[str]) -> Optional[str]:
    if value is None:
        return None
    options = tuple(choices)
    if value not in options:
        raise ValueError(f"{name} must be one of {', '.join(options)}; got {value!r}")
    return value


def _user_timeline(
    suffix: str,
    user_id: Optional[ID],
    username: Optional[str],
    count: Optional[int],
    cursor: Optional[str],
) -> EndpointRequest:
    """User timelines take a user ID in the path. With only a username, the API accepts
    ``/user/-1/...?username=<handle>`` and resolves the handle itself (one extra lookup on
    the server side, so passing the ID is a little faster)."""
    params: Dict[str, QueryValue] = {}
    if user_id is not None and user_id != "":
        uid = _numeric_id(user_id, "user_id")
    elif username is not None:
        uid = "-1"
        params["username"] = _username(username)
    else:
        raise ValueError("Provide either user_id or username.")
    params.update(_paging(count, cursor))
    return EndpointRequest(f"/user/{uid}/{suffix}", params)


# Users ---------------------------------------------------------------------


def user_by_username(username: str) -> EndpointRequest:
    return EndpointRequest(f"/user/by/username/{_seg(_username(username))}")


def user_by_id(user_id: ID) -> EndpointRequest:
    return EndpointRequest(f"/user/{_numeric_id(user_id, 'user_id')}")


def username_to_id(username: str) -> EndpointRequest:
    return EndpointRequest(f"/username/to/id/{_seg(_username(username))}")


def users_by_ids(user_ids: Iterable[ID]) -> EndpointRequest:
    if isinstance(user_ids, (str, bytes)):
        raise TypeError("user_ids must be a list of IDs, not a single string")
    ids = [_numeric_id(u, "each user id") for u in user_ids]
    if not ids:
        raise ValueError("user_ids must contain at least one ID")
    if len(ids) > MAX_USERS_PER_LOOKUP:
        raise ValueError(
            f"user_ids accepts at most {MAX_USERS_PER_LOOKUP} IDs per call, got {len(ids)}"
        )
    return EndpointRequest("/user/users/by/ids", {"ids": ",".join(ids)})


USER_TIMELINES = {
    "tweets": "tweets",
    "tweets_and_replies": "tweetsAndReplies",
    "media": "media",
    "followers": "followers",
    "following": "followings",
    "verified_followers": "verifiedFollowers",
}


def user_timeline(
    kind: str,
    user_id: Optional[ID],
    username: Optional[str],
    count: Optional[int],
    cursor: Optional[str],
) -> EndpointRequest:
    """``kind`` is a key of USER_TIMELINES, e.g. "followers"."""
    return _user_timeline(USER_TIMELINES[kind], user_id, username, count, cursor)


# Tweets --------------------------------------------------------------------


def tweet(tweet_id: ID, ranking_mode: Optional[str], cursor: Optional[str]) -> EndpointRequest:
    params: Dict[str, QueryValue] = {}
    mode = _choice(ranking_mode, "ranking_mode", RANKING_MODES)
    if mode:
        params["rankingMode"] = mode
    if cursor:
        params["cursor"] = cursor
    return EndpointRequest(f"/tweet/{_numeric_id(tweet_id, 'tweet_id')}", params)


def _tweet_sub(
    suffix: str, tweet_id: ID, count: Optional[int], cursor: Optional[str]
) -> EndpointRequest:
    return EndpointRequest(
        f"/tweet/{_numeric_id(tweet_id, 'tweet_id')}/{suffix}", _paging(count, cursor)
    )


def tweet_retweeters(tweet_id: ID, count: Optional[int], cursor: Optional[str]) -> EndpointRequest:
    return _tweet_sub("retweets", tweet_id, count, cursor)


def tweet_likers(tweet_id: ID, count: Optional[int], cursor: Optional[str]) -> EndpointRequest:
    return _tweet_sub("favorites", tweet_id, count, cursor)


def tweet_quotes(tweet_id: ID, count: Optional[int], cursor: Optional[str]) -> EndpointRequest:
    return _tweet_sub("quotes", tweet_id, count, cursor)


# Search --------------------------------------------------------------------


def search_tweets(
    query: str, category: Optional[str], count: Optional[int], cursor: Optional[str]
) -> EndpointRequest:
    params: Dict[str, QueryValue] = {"searchItem": _non_empty(query, "query")}
    cat = _choice(category, "category", SEARCH_CATEGORIES)
    if cat:
        params["category"] = cat
    params.update(_paging(count, cursor))
    return EndpointRequest("/search", params)


# Lists ---------------------------------------------------------------------


def list_details(list_id: ID) -> EndpointRequest:
    return EndpointRequest("/lists/details", {"listId": _numeric_id(list_id, "list_id")})


def list_tweets(list_id: ID, count: Optional[int], cursor: Optional[str]) -> EndpointRequest:
    params: Dict[str, QueryValue] = {"listId": _numeric_id(list_id, "list_id")}
    params.update(_paging(count, cursor))
    return EndpointRequest("/lists/tweets", params)


def list_members(list_id: ID, count: Optional[int], cursor: Optional[str]) -> EndpointRequest:
    params: Dict[str, QueryValue] = {"listId": _numeric_id(list_id, "list_id")}
    params.update(_paging(count, cursor))
    return EndpointRequest("/lists/members", params)


# Communities ---------------------------------------------------------------


def community(community_id: ID) -> EndpointRequest:
    return EndpointRequest(f"/communities/{_numeric_id(community_id, 'community_id')}")


def community_tweets(
    community_id: ID, count: Optional[int], cursor: Optional[str]
) -> EndpointRequest:
    return EndpointRequest(
        f"/communities/{_numeric_id(community_id, 'community_id')}/tweets",
        _paging(count, cursor),
    )


def community_search(query: str, count: Optional[int], cursor: Optional[str]) -> EndpointRequest:
    return EndpointRequest(
        f"/communities/search/{_seg(_non_empty(query, 'query'))}", _paging(count, cursor)
    )


# Trends --------------------------------------------------------------------


def trends(location_id: ID) -> EndpointRequest:
    if isinstance(location_id, bool):
        raise TypeError("location_id must be a numeric WOEID")
    text = str(location_id).strip()
    if not _WOEID.match(text):
        raise ValueError(f"location_id must be a numeric WOEID, got {location_id!r}")
    return EndpointRequest(f"/trends/{text}")


def trend_locations() -> EndpointRequest:
    return EndpointRequest("/misc/locations")
