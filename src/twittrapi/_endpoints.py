"""Request builders for every TwittrAPI endpoint.

Each function validates its arguments and returns an :class:`EndpointRequest` (path plus query
parameters). The sync and async resource classes both call these, so the mapping from Python
arguments to the HTTP request lives in one place.

The endpoints here return X's raw GraphQL JSON (the batch lookups answer a small JSON object
built by the API around X's items). They are GET requests, except tweet likers, which
is a POST with the author's cookie and a proxy in a JSON body. The account actions
(``/client/...``, POST with the session in the body) are in :mod:`._account_endpoints`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Set, Union
from urllib.parse import quote

ID = Union[str, int]
QueryValue = Union[str, int]

_NUMERIC = re.compile(r"^\d{1,30}$")
_WOEID = re.compile(r"^\d{1,12}$")
_SPACE_ID = re.compile(r"^[A-Za-z0-9]{1,32}$")
_HANDLE = re.compile(r"^[A-Za-z0-9_]{1,15}$")

MAX_USERS_PER_LOOKUP = 500
MAX_FRIENDSHIP_TARGETS = 50
MAX_ABOUT_USERNAMES = 20
# X treats count as a hint (pages can be larger or smaller); TwittrAPI accepts 1..100.
MAX_COUNT = 100
SEARCH_CATEGORIES = ("Top", "Latest", "People", "Photos", "Videos")
RANKING_MODES = ("Relevance", "Recency", "Likes")


@dataclass(frozen=True)
class EndpointRequest:
    path: str
    params: Dict[str, QueryValue] = field(default_factory=dict)
    method: str = "GET"
    # JSON body, sent only with POST.
    body: Optional[Dict[str, Any]] = None
    # False for account actions that change something (post, like, follow, ...): those are
    # retried only when the request cannot have reached the API, so a retry never repeats
    # an action. See _base.can_retry_error.
    idempotent: bool = True


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
    text = value.strip()
    if text.startswith("@"):
        text = text[1:].strip()
    if not text:
        raise ValueError("username must not be empty")
    return text


def _handle(value: str, name: str) -> str:
    """A handle as X allows it: 1 to 15 letters, digits or underscores (``@`` optional)."""
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string, got {type(value).__name__}")
    text = value.strip()
    if text.startswith("@"):
        text = text[1:].strip()
    if not _HANDLE.match(text):
        raise ValueError(
            f"{name} must be a username of 1 to 15 letters, digits or underscores, got {value!r}"
        )
    return text


def _handles(values: Iterable[str], name: str, limit: int) -> str:
    """A list of handles as a comma-separated string: ``@`` stripped, duplicates dropped
    (case-insensitive, first spelling kept), at most ``limit`` after that."""
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{name} must be a list of usernames, not a single string")
    seen: Set[str] = set()
    out: List[str] = []
    for value in values:
        handle = _handle(value, f"each username in {name}")
        if handle.lower() not in seen:
            seen.add(handle.lower())
            out.append(handle)
    if not out:
        raise ValueError(f"{name} must contain at least one username")
    if len(out) > limit:
        raise ValueError(
            f"{name} accepts at most {limit} different usernames per call, got {len(out)}"
        )
    return ",".join(out)


def _bool_param(value: Optional[bool], name: str) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be True or False, got {type(value).__name__}")
    return "true" if value else "false"


def _non_empty(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _paging(count: Optional[int], cursor: Optional[str]) -> Dict[str, QueryValue]:
    params: Dict[str, QueryValue] = {}
    if count is not None:
        if (
            isinstance(count, bool)
            or not isinstance(count, int)
            or count < 1
            or count > MAX_COUNT
        ):
            raise ValueError(f"count must be an integer from 1 to {MAX_COUNT}, got {count!r}")
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


def friendships_batch(source: str, targets: Iterable[str]) -> EndpointRequest:
    return EndpointRequest(
        "/user/friendships/batch",
        {
            "source_screen_name": _handle(source, "source"),
            "target_screen_names": _handles(targets, "targets", MAX_FRIENDSHIP_TARGETS),
        },
    )


def about_batch(usernames: Iterable[str]) -> EndpointRequest:
    return EndpointRequest(
        "/user/about/batch", {"usernames": _handles(usernames, "usernames", MAX_ABOUT_USERNAMES)}
    )


USER_TIMELINES = {
    "tweets": "tweets",
    "tweets_and_replies": "tweetsAndReplies",
    "media": "media",
    "followers": "followers",
    "following": "followings",
    "verified_followers": "verifiedFollowers",
    "affiliates": "affiliates",
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


def _conversation(
    suffix: str,
    tweet_id: ID,
    ranking_mode: Optional[str],
    include_promoted_content: Optional[bool],
    cursor: Optional[str],
) -> EndpointRequest:
    params: Dict[str, QueryValue] = {}
    mode = _choice(ranking_mode, "ranking_mode", RANKING_MODES)
    if mode:
        params["rankingMode"] = mode
    promoted = _bool_param(include_promoted_content, "include_promoted_content")
    if promoted is not None:
        params["includePromotedContent"] = promoted
    if cursor:
        params["cursor"] = cursor
    return EndpointRequest(f"/tweet/{_numeric_id(tweet_id, 'tweet_id')}/{suffix}", params)


def tweet_replies(
    tweet_id: ID,
    ranking_mode: Optional[str],
    include_promoted_content: Optional[bool],
    cursor: Optional[str],
) -> EndpointRequest:
    return _conversation("replies", tweet_id, ranking_mode, include_promoted_content, cursor)


def tweet_thread(
    tweet_id: ID, ranking_mode: Optional[str], include_promoted_content: Optional[bool]
) -> EndpointRequest:
    return _conversation("thread", tweet_id, ranking_mode, include_promoted_content, None)


def _tweet_sub(
    suffix: str, tweet_id: ID, count: Optional[int], cursor: Optional[str]
) -> EndpointRequest:
    return EndpointRequest(
        f"/tweet/{_numeric_id(tweet_id, 'tweet_id')}/{suffix}", _paging(count, cursor)
    )


def tweet_retweeters(tweet_id: ID, count: Optional[int], cursor: Optional[str]) -> EndpointRequest:
    return _tweet_sub("retweets", tweet_id, count, cursor)


def tweet_likers(
    tweet_id: ID, cookie: str, proxy: str, count: Optional[int], cursor: Optional[str]
) -> EndpointRequest:
    """POST with the cookie of the account that posted the tweet and a proxy in the body.
    X shows likers only to the author. Paging goes in the body too."""
    path = f"/tweet/{_numeric_id(tweet_id, 'tweet_id')}/favorites"
    body: Dict[str, Any] = {
        "cookie": _non_empty(cookie, "cookie"),
        "proxy": _non_empty(proxy, "proxy"),
    }
    body.update(_paging(count, cursor))
    return EndpointRequest(path, method="POST", body=body)


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


def community_about(community_id: ID) -> EndpointRequest:
    return EndpointRequest(f"/communities/{_numeric_id(community_id, 'community_id')}/about")


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


# Spaces --------------------------------------------------------------------


def space(space_id: str) -> EndpointRequest:
    if not isinstance(space_id, str):
        raise TypeError(f"space_id must be a string, got {type(space_id).__name__}")
    text = space_id.strip()
    if not _SPACE_ID.match(text):
        raise ValueError(
            f"space_id must be 1 to 32 letters and digits (as in x.com/i/spaces/<id>), "
            f"got {space_id!r}"
        )
    return EndpointRequest(f"/spaces/{text}")


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
