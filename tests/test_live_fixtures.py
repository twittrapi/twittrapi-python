"""Pagination against trimmed real TwittrAPI responses (tests/fixtures/live, captured 2026-10-10).

Each fixture is ``{"request": ..., "capturedAt": ..., "response": <API body>}``; only
``response`` is served. No network access.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict

import pytest

from twittrapi import MAX_COUNT, extract_bottom_cursor
from twittrapi.pagination import count_content_entries, page_is_empty

from .conftest import MockAPI, json_response

LIVE = Path(__file__).parent / "fixtures" / "live"


def live(name: str) -> Any:
    return json.loads((LIVE / f"{name}.json").read_text(encoding="utf-8"))["response"]


def entries_of(data: Any) -> list:
    out: list = []
    stack = [data]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            if isinstance(node.get("entries"), list):
                out.extend(e for e in node["entries"] if isinstance(e, dict) and "entryId" in e)
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return out


# --- cursor extraction --------------------------------------------------------


def test_followers_bottom_before_top() -> None:
    data = live("user-userid-followers")
    cursors = [e for e in entries_of(data) if e["entryId"].startswith("cursor-")]
    assert [e["content"]["cursorType"] for e in cursors] == ["Bottom", "Top"]
    bottom = cursors[0]["content"]["value"]
    assert extract_bottom_cursor(data) == bottom
    assert not extract_bottom_cursor(data).startswith("-1|")


def test_user_tweets_top_first_still_bottom() -> None:
    data = live("user-userid-tweets")
    bottom = [e for e in entries_of(data) if e["entryId"].startswith("cursor-bottom-")][0]
    assert extract_bottom_cursor(data) == bottom["content"]["value"]


def test_tweet_detail_bottom_cursor() -> None:
    data = live("tweet-tweetid")
    last = data["data"]["threaded_conversation_with_injections_v2"]["instructions"][1]["entries"][-1]
    content = last["content"]
    value = content.get("value") or content["itemContent"]["value"]
    assert extract_bottom_cursor(data) == value


def test_search_wrapper() -> None:
    data = live("search")
    assert data["category"] == "Latest"
    bottom = [e for e in data["entries"][0]["entries"] if e["entryId"].startswith("cursor-bottom-")][0]
    assert extract_bottom_cursor(data) == bottom["content"]["value"]
    assert count_content_entries(data) == (2, 1)
    assert not page_is_empty(data)


@pytest.mark.parametrize(
    "name, path",
    [
        ("communities-search-searchterm", ("data", "communities_search_slice")),
        ("communities-communityid-members", ("data", "communityResults", "result", "members_slice")),
        ("jobs-search-searchterm", ("data", "job_search")),
    ],
)
def test_slice_next_cursor(name: str, path: tuple) -> None:
    data = live(name)
    node = data
    for key in path:
        node = node[key]
    assert extract_bottom_cursor(data) == node["slice_info"]["next_cursor"]
    assert not page_is_empty(data)


def test_moderators_single_page_has_no_cursor() -> None:
    assert extract_bottom_cursor(live("communities-communityid-moderators")) is None


@pytest.mark.parametrize("name", ["user-userid-likes", "tweet-tweetid-favorites"])
def test_empty_timelines_have_no_cursor(name: str) -> None:
    data = live(name)
    assert extract_bottom_cursor(data) is None
    assert count_content_entries(data) == (0, 0)


def test_article_with_empty_tweet_results() -> None:
    data = copy.deepcopy(live("user-userid-articles"))
    entries = data["data"]["user"]["result"]["timeline"]["timeline"]["instructions"][0]["entries"]
    deleted: Dict[str, Any] = copy.deepcopy(entries[0])
    deleted["entryId"] = "tweet-1"
    deleted["content"]["itemContent"]["tweet_results"] = {}
    entries.insert(0, deleted)
    assert extract_bottom_cursor(data) == "DAABCgABHUS5rv1___sKAAIAAAAAAAAAAAgAAwAAAAIAAA"
    assert count_content_entries(data) == (1, 2)


# --- paginate() on real pages ---------------------------------------------------


def test_paginate_likes_stops_after_empty_page() -> None:
    api = MockAPI(json_response(live("user-userid-likes")))
    with api.client() as client:
        pages = list(client.paginate(client.users.tweets, "2244994945", max_pages=None))
    assert len(pages) == 1 and len(api.requests) == 1


def test_paginate_favorites_stops_after_terminate() -> None:
    api = MockAPI(json_response(live("tweet-tweetid-favorites")))
    with api.client() as client:
        pages = list(
            client.paginate(
                client.tweets.likers,
                "2019881223666233717",
                cookie="auth_token=a; ct0=b",
                proxy="http://u:p@h:1",
                max_pages=None,
            )
        )
    assert len(pages) == 1 and len(api.requests) == 1


def test_paginate_followers_uses_bottom_cursor_not_count() -> None:
    first = live("user-userid-followers")
    bottom = extract_bottom_cursor(first)
    empty_tail = copy.deepcopy(first)
    instr = empty_tail["data"]["user"]["result"]["timeline"]["timeline"]["instructions"]
    for ins in instr:
        if "entries" in ins:
            ins["entries"] = [e for e in ins["entries"] if e["entryId"].startswith("cursor-")]
            for e in ins["entries"]:
                if e["content"]["cursorType"] == "Bottom":
                    e["content"]["value"] = "1000000000000000000|1"
    api = MockAPI(json_response(first), json_response(empty_tail))
    with api.client() as client:
        pages = list(client.paginate(client.users.followers, "2244994945", count=20, max_pages=None))
    assert len(pages) == 2
    assert "cursor" not in api.requests[0].url.params
    assert api.requests[1].url.params["cursor"] == bottom
    assert api.requests[1].url.params["count"] == "20"


def test_paginate_communities_search_stops_on_empty_slice() -> None:
    first = live("communities-search-searchterm")
    empty = copy.deepcopy(first)
    empty["data"]["communities_search_slice"]["items_results"] = []
    empty["data"]["communities_search_slice"]["slice_info"]["next_cursor"] = "next-but-empty"
    api = MockAPI(json_response(first), json_response(empty), json_response(first))
    with api.client() as client:
        pages = list(client.paginate(client.communities.search, "openai", max_pages=None))
    assert len(pages) == 2
    assert api.requests[1].url.params["cursor"] == extract_bottom_cursor(first)


# --- count limits -----------------------------------------------------------------


def test_count_bounds() -> None:
    assert MAX_COUNT == 100
    api = MockAPI()
    with api.client() as client:
        client.users.followers("12", count=MAX_COUNT)
        assert api.last.url.params["count"] == "100"
        for bad in (0, MAX_COUNT + 1, 500):
            with pytest.raises(ValueError, match="1 to 100"):
                client.users.followers("12", count=bad)
    assert len(api.requests) == 1


def test_user_id_wins_over_username() -> None:
    api = MockAPI()
    with api.client() as client:
        client.users.followers(user_id="2244994945", username="@XDevelopers")
    assert api.last.url.path == "/user/2244994945/followers"
    assert "username" not in api.last.url.params


def test_username_only_strips_one_at() -> None:
    api = MockAPI()
    with api.client() as client:
        client.users.followers(username=" @XDevelopers ")
    assert api.last.url.path == "/user/-1/followers"
    assert api.last.url.params["username"] == "XDevelopers"
