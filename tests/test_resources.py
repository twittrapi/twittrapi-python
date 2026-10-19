"""Every resource method, sync and async, builds the expected path and query."""

from __future__ import annotations

import inspect
import json
from typing import Any, Callable, Dict

import pytest

from twittrapi import AsyncTwittrAPI, TwittrAPI

from .conftest import MockAPI, json_response

UID = "44196397"
TID = "1585841080431321088"
COOKIE = "auth_token=a; ct0=b"
PROXY = "http://user:pass@1.2.3.4:8080"

# (call, expected path, expected query params)
CASES = [
    # users
    (lambda c: c.users.get_by_username("@elonmusk"), "/user/by/username/elonmusk", {}),
    (lambda c: c.users.get_by_id(44196397), f"/user/{UID}", {}),
    (lambda c: c.users.username_to_id(" jack "), "/username/to/id/jack", {}),
    (lambda c: c.users.get_many([1, "2", 3]), "/user/users/by/ids", {"ids": "1,2,3"}),
    (lambda c: c.users.tweets(UID), f"/user/{UID}/tweets", {}),
    (
        lambda c: c.users.tweets(username="@jack", count=50, cursor="abc"),
        "/user/-1/tweets",
        {"username": "jack", "count": "50", "cursor": "abc"},
    ),
    (lambda c: c.users.tweets_and_replies(UID, count=10), f"/user/{UID}/tweetsAndReplies", {"count": "10"}),
    (lambda c: c.users.tweets_and_replies(username="jack"), "/user/-1/tweetsAndReplies", {"username": "jack"}),
    (lambda c: c.users.media(UID, cursor="c1"), f"/user/{UID}/media", {"cursor": "c1"}),
    (lambda c: c.users.media(username="jack"), "/user/-1/media", {"username": "jack"}),
    (lambda c: c.users.followers(UID, count=100), f"/user/{UID}/followers", {"count": "100"}),
    (lambda c: c.users.followers(username="jack"), "/user/-1/followers", {"username": "jack"}),
    (lambda c: c.users.following(UID), f"/user/{UID}/followings", {}),
    (lambda c: c.users.following(username="jack"), "/user/-1/followings", {"username": "jack"}),
    (lambda c: c.users.verified_followers(UID), f"/user/{UID}/verifiedFollowers", {}),
    (
        lambda c: c.users.verified_followers(username="jack", count=20),
        "/user/-1/verifiedFollowers",
        {"username": "jack", "count": "20"},
    ),
    (lambda c: c.users.affiliates(UID), f"/user/{UID}/affiliates", {}),
    (
        lambda c: c.users.affiliates(username="@XDevelopers", count=100, cursor="af"),
        "/user/-1/affiliates",
        {"username": "XDevelopers", "count": "100", "cursor": "af"},
    ),
    (
        lambda c: c.users.friendships_batch("@jack", ["elonmusk", "@XDevelopers", "ELONMUSK", " x "]),
        "/user/friendships/batch",
        {"source_screen_name": "jack", "target_screen_names": "elonmusk,XDevelopers,x"},
    ),
    (
        lambda c: c.users.friendships_batch("jack", (f"user{i}" for i in range(50))),
        "/user/friendships/batch",
        {"source_screen_name": "jack", "target_screen_names": ",".join(f"user{i}" for i in range(50))},
    ),
    (lambda c: c.users.about_batch(["@jack", "Jack", "XDevelopers"]), "/user/about/batch",
     {"usernames": "jack,XDevelopers"}),
    (lambda c: c.users.about_batch([f"u_{i}" for i in range(20)]), "/user/about/batch",
     {"usernames": ",".join(f"u_{i}" for i in range(20))}),
    # user_id wins over username when both are given
    (lambda c: c.users.tweets(UID, username="jack"), f"/user/{UID}/tweets", {}),
    # tweets
    (lambda c: c.tweets.get(TID), f"/tweet/{TID}", {}),
    (
        lambda c: c.tweets.get(int(TID), ranking_mode="Recency", cursor="x"),
        f"/tweet/{TID}",
        {"rankingMode": "Recency", "cursor": "x"},
    ),
    (lambda c: c.tweets.replies(TID), f"/tweet/{TID}/replies", {}),
    (
        lambda c: c.tweets.replies(int(TID), ranking_mode="Likes", include_promoted_content=True, cursor="r"),
        f"/tweet/{TID}/replies",
        {"rankingMode": "Likes", "includePromotedContent": "true", "cursor": "r"},
    ),
    (lambda c: c.tweets.thread(TID), f"/tweet/{TID}/thread", {}),
    (
        lambda c: c.tweets.thread(TID, ranking_mode="Recency", include_promoted_content=False),
        f"/tweet/{TID}/thread",
        {"rankingMode": "Recency", "includePromotedContent": "false"},
    ),
    (lambda c: c.tweets.retweeters(TID, count=40), f"/tweet/{TID}/retweets", {"count": "40"}),
    # likers is a POST: paging goes in the body, see test_likers_posts_json_body
    (lambda c: c.tweets.likers(TID, cookie=COOKIE, proxy=PROXY, cursor="y"), f"/tweet/{TID}/favorites", {}),
    (lambda c: c.tweets.quotes(TID), f"/tweet/{TID}/quotes", {}),
    # search
    (lambda c: c.search.tweets("python"), "/search", {"searchItem": "python"}),
    (
        lambda c: c.search.tweets('from:jack "hello world" lang:en', category="Latest", count=20, cursor="z"),
        "/search",
        {"searchItem": 'from:jack "hello world" lang:en', "category": "Latest", "count": "20", "cursor": "z"},
    ),
    # lists
    (lambda c: c.lists.details(1234), "/lists/details", {"listId": "1234"}),
    (lambda c: c.lists.tweets("1234", count=5), "/lists/tweets", {"listId": "1234", "count": "5"}),
    (lambda c: c.lists.members("1234", cursor="m"), "/lists/members", {"listId": "1234", "cursor": "m"}),
    # communities
    (lambda c: c.communities.get(1500), "/communities/1500", {}),
    (lambda c: c.communities.about(1500), "/communities/1500/about", {}),
    (lambda c: c.communities.tweets("1500", count=10), "/communities/1500/tweets", {"count": "10"}),
    (lambda c: c.communities.search("open source"), "/communities/search/open%20source", {}),
    (lambda c: c.communities.search("a/b", cursor="n"), "/communities/search/a%2Fb", {"cursor": "n"}),
    # spaces
    (lambda c: c.spaces.get("1YqKDqWqdPLsV"), "/spaces/1YqKDqWqdPLsV", {}),
    (lambda c: c.spaces.get(" 1OdKrjPXyRVJX "), "/spaces/1OdKrjPXyRVJX", {}),
    # trends
    (lambda c: c.trends.get(), "/trends/1", {}),
    (lambda c: c.trends.get(23424977), "/trends/23424977", {}),
    (lambda c: c.trends.locations(), "/misc/locations", {}),
]


def _check(api: MockAPI, path: str, params: Dict[str, str]) -> None:
    assert len(api.requests) == 1
    req = api.last
    assert req.url.raw_path.decode().split("?")[0] == path
    assert dict(req.url.params) == params


LIKERS_BODY = {"cookie": COOKIE, "proxy": PROXY, "count": 100, "cursor": "y"}


def _check_likers(api: MockAPI) -> None:
    assert len(api.requests) == 1
    req = api.last
    assert req.method == "POST"
    assert req.url.raw_path.decode() == f"/tweet/{TID}/favorites"
    assert req.headers["content-type"] == "application/json"
    assert json.loads(req.content) == LIKERS_BODY


def test_likers_posts_json_body(api: MockAPI) -> None:
    api.client().tweets.likers(TID, cookie=COOKIE, proxy=PROXY, count=100, cursor="y")
    _check_likers(api)


async def test_async_likers_posts_json_body(api: MockAPI) -> None:
    await api.async_client().tweets.likers(TID, cookie=COOKIE, proxy=PROXY, count=100, cursor="y")
    _check_likers(api)


def test_other_methods_send_get_without_body(api: MockAPI) -> None:
    api.client().tweets.retweeters(TID)
    assert api.last.method == "GET"
    assert api.last.content == b""


def test_likers_paginate_sends_cursor_in_body() -> None:
    first = {"data": {"timeline": {"instructions": [{"type": "TimelineAddEntries", "entries": [
        {"entryId": "user-1", "content": {}},
        {"entryId": "cursor-bottom-1", "content": {"cursorType": "Bottom", "value": "c1"}},
    ]}]}}}
    last = {"data": {"timeline": {"instructions": [{"type": "TimelineAddEntries", "entries": [
        {"entryId": "user-2", "content": {}},
    ]}]}}}
    api = MockAPI(json_response(first), json_response(last))
    client = api.client()
    pages = list(client.paginate(client.tweets.likers, TID, cookie=COOKIE, proxy=PROXY, count=50))
    assert len(pages) == 2
    bodies = [json.loads(r.content) for r in api.requests]
    assert [b.get("cursor") for b in bodies] == [None, "c1"]
    assert all(b["count"] == 50 and b["cookie"] == COOKIE for b in bodies)
    assert all(r.method == "POST" and not r.url.params for r in api.requests)


@pytest.mark.parametrize("call,path,params", CASES)
def test_sync(api: MockAPI, call: Callable[[Any], Any], path: str, params: Dict[str, str]) -> None:
    result = call(api.client())
    assert result == {"ok": True}
    _check(api, path, params)


@pytest.mark.parametrize("call,path,params", CASES)
async def test_async(api: MockAPI, call: Callable[[Any], Any], path: str, params: Dict[str, str]) -> None:
    result = await call(api.async_client())
    assert result == {"ok": True}
    _check(api, path, params)


def _public_methods(obj: Any) -> Dict[str, Any]:
    return {
        name: getattr(obj, name)
        for name in dir(obj)
        if not name.startswith("_") and callable(getattr(obj, name))
    }


@pytest.mark.parametrize("resource", ["users", "tweets", "search", "lists", "communities", "spaces", "trends"])
def test_async_parity(resource: str) -> None:
    sync_res = getattr(TwittrAPI(api_key="k"), resource)
    async_res = getattr(AsyncTwittrAPI(api_key="k"), resource)
    sync_methods = _public_methods(sync_res)
    async_methods = _public_methods(async_res)
    assert sync_methods.keys() == async_methods.keys()
    for name, method in async_methods.items():
        assert inspect.iscoroutinefunction(method), name
        assert inspect.signature(method) == inspect.signature(sync_methods[name]), name


def test_expected_method_names() -> None:
    c = TwittrAPI(api_key="k")
    assert set(_public_methods(c.users)) == {
        "get_by_username", "get_by_id", "username_to_id", "get_many", "tweets",
        "tweets_and_replies", "media", "followers", "following", "verified_followers",
        "affiliates", "friendships_batch", "about_batch",
    }
    assert set(_public_methods(c.tweets)) == {"get", "replies", "thread", "retweeters", "likers", "quotes"}
    assert set(_public_methods(c.search)) == {"tweets"}
    assert set(_public_methods(c.lists)) == {"details", "tweets", "members"}
    assert set(_public_methods(c.communities)) == {"get", "about", "tweets", "search"}
    assert set(_public_methods(c.spaces)) == {"get"}
    assert set(_public_methods(c.trends)) == {"get", "locations"}


@pytest.mark.parametrize(
    "call,exc",
    [
        (lambda c: c.users.tweets(), ValueError),
        (lambda c: c.users.followers(username="  @ "), ValueError),
        (lambda c: c.users.get_by_id("jack"), ValueError),
        (lambda c: c.users.get_by_username(""), ValueError),
        (lambda c: c.users.get_many([]), ValueError),
        (lambda c: c.users.get_many([str(i) for i in range(501)]), ValueError),
        (lambda c: c.users.get_many("123"), TypeError),
        (lambda c: c.tweets.get("12a"), ValueError),
        (lambda c: c.tweets.get(True), TypeError),
        (lambda c: c.tweets.get(TID, ranking_mode="Newest"), ValueError),
        (lambda c: c.tweets.likers("12a", cookie=COOKIE, proxy=PROXY), ValueError),
        (lambda c: c.tweets.likers(TID, cookie=" ", proxy=PROXY), ValueError),
        (lambda c: c.tweets.likers(TID, cookie=COOKIE, proxy=""), ValueError),
        (lambda c: c.tweets.likers(TID, cookie=None, proxy=PROXY), ValueError),
        (lambda c: c.tweets.likers(TID, cookie=COOKIE, proxy=PROXY, count=101), ValueError),
        (lambda c: c.search.tweets(""), ValueError),
        (lambda c: c.search.tweets("x", category="Recent"), ValueError),
        (lambda c: c.search.tweets("x", count=0), ValueError),
        (lambda c: c.lists.details("abc"), ValueError),
        (lambda c: c.communities.search("  "), ValueError),
        (lambda c: c.trends.get("us"), ValueError),
        # new in 1.2.0
        (lambda c: c.users.affiliates(), ValueError),
        (lambda c: c.users.affiliates(UID, count=0), ValueError),
        (lambda c: c.users.affiliates(username="jack", count=101), ValueError),
        (lambda c: c.users.affiliates("jack"), ValueError),
        (lambda c: c.users.friendships_batch("jack", []), ValueError),
        (lambda c: c.users.friendships_batch("jack", "elonmusk"), TypeError),
        (lambda c: c.users.friendships_batch("jack", ["bad-handle"]), ValueError),
        (lambda c: c.users.friendships_batch("jack", ["a" * 16]), ValueError),
        (lambda c: c.users.friendships_batch("jack", ["@"]), ValueError),
        (lambda c: c.users.friendships_batch("jack", [12]), TypeError),
        (lambda c: c.users.friendships_batch("", ["x"]), ValueError),
        (lambda c: c.users.friendships_batch("not valid", ["x"]), ValueError),
        (lambda c: c.users.friendships_batch("jack", [f"user{i}" for i in range(51)]), ValueError),
        (lambda c: c.users.about_batch([]), ValueError),
        (lambda c: c.users.about_batch("jack"), TypeError),
        (lambda c: c.users.about_batch(["jack", "a.b"]), ValueError),
        (lambda c: c.users.about_batch([f"u{i}" for i in range(21)]), ValueError),
        (lambda c: c.tweets.replies("12a"), ValueError),
        (lambda c: c.tweets.replies(TID, ranking_mode="Newest"), ValueError),
        (lambda c: c.tweets.replies(TID, include_promoted_content="yes"), TypeError),
        (lambda c: c.tweets.thread("abc"), ValueError),
        (lambda c: c.tweets.thread(TID, ranking_mode="Top"), ValueError),
        (lambda c: c.communities.about("abc"), ValueError),
        (lambda c: c.spaces.get(""), ValueError),
        (lambda c: c.spaces.get("1YqK-DqWq"), ValueError),
        (lambda c: c.spaces.get("a/b"), ValueError),
        (lambda c: c.spaces.get("a" * 33), ValueError),
        (lambda c: c.spaces.get(123), TypeError),
    ],
)
def test_client_side_validation(api: MockAPI, call: Callable[[Any], Any], exc: type) -> None:
    with pytest.raises(exc):
        call(api.client())
    assert api.requests == []


def test_get_many_accepts_exactly_500(api: MockAPI) -> None:
    api.client().users.get_many(range(1, 501))
    assert len(api.last.url.params["ids"].split(",")) == 500


def test_batch_limits_count_distinct_handles(api: MockAPI) -> None:
    # 60 entries but only 50 different handles once case-insensitive duplicates are dropped
    targets = [f"user{i}" for i in range(50)] + [f"USER{i}" for i in range(10)]
    api.client().users.friendships_batch("jack", targets)
    assert len(api.last.url.params["target_screen_names"].split(",")) == 50
    api.client().users.about_batch(["jack"] * 30)
    assert api.last.url.params["usernames"] == "jack"


def test_thread_has_no_cursor() -> None:
    assert "cursor" not in inspect.signature(TwittrAPI(api_key="k").tweets.thread).parameters
