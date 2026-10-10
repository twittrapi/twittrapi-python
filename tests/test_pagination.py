from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx
import pytest

from twittrapi import extract_bottom_cursor
from twittrapi.pagination import count_content_entries

from .conftest import MockAPI, json_response


def tweet_entry(i: int) -> Dict[str, Any]:
    return {
        "entryId": f"tweet-{i}",
        "sortIndex": str(1000 - i),
        "content": {
            "entryType": "TimelineTimelineItem",
            "itemContent": {"itemType": "TimelineTweet", "tweet_results": {"result": {"rest_id": str(i)}}},
        },
    }


def cursor_entry(kind: str, value: str) -> Dict[str, Any]:
    return {
        "entryId": f"cursor-{kind.lower()}-{value}",
        "sortIndex": "1",
        "content": {"entryType": "TimelineTimelineCursor", "__typename": "TimelineTimelineCursor",
                    "value": value, "cursorType": kind},
    }


def user_timeline(entries: List[Dict[str, Any]], extra: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    instructions: List[Dict[str, Any]] = [
        {"type": "TimelineClearCache"},
        {"type": "TimelineAddEntries", "entries": entries},
    ]
    instructions += extra or []
    return {"data": {"user": {"result": {"timeline": {"timeline": {"instructions": instructions}}}}}}


# --- extract_bottom_cursor ---------------------------------------------------


def test_finds_bottom_not_top() -> None:
    data = user_timeline([tweet_entry(1), cursor_entry("Top", "TOP"), cursor_entry("Bottom", "BOTTOM")])
    assert extract_bottom_cursor(data) == "BOTTOM"


def test_finds_bottom_in_replace_entry() -> None:
    data = user_timeline(
        [tweet_entry(1)],
        extra=[
            {"type": "TimelineReplaceEntry", "entry_id_to_replace": "cursor-top-x", "entry": cursor_entry("Top", "T2")},
            {"type": "TimelineReplaceEntry", "entry_id_to_replace": "cursor-bottom-x", "entry": cursor_entry("Bottom", "B2")},
        ],
    )
    assert extract_bottom_cursor(data) == "B2"


def test_finds_cursor_in_item_content() -> None:
    # TweetDetail style: cursor inside itemContent of a module item.
    data = {"data": {"threaded_conversation_with_injections_v2": {"instructions": [{
        "type": "TimelineAddEntries",
        "entries": [tweet_entry(1), {
            "entryId": "cursor-bottom-123",
            "content": {"entryType": "TimelineTimelineItem", "itemContent": {
                "itemType": "TimelineTimelineCursor", "value": "DETAIL", "cursorType": "Bottom"}},
        }],
    }]}}}
    assert extract_bottom_cursor(data) == "DETAIL"


def test_entry_id_without_cursor_type() -> None:
    data = {"entries": [tweet_entry(1), {"entryId": "cursor-bottom-9", "content": {"value": "BYID"}}]}
    assert extract_bottom_cursor(data) == "BYID"


def test_snake_case_cursor_type() -> None:
    assert extract_bottom_cursor({"x": [{"cursor_type": "Bottom", "value": "SNAKE"}]}) == "SNAKE"


def test_next_cursor_field() -> None:
    assert extract_bottom_cursor({"users": [], "next_cursor": "NC"}) == "NC"
    assert extract_bottom_cursor({"users": [], "next_cursor": "0"}) is None


def test_no_cursor() -> None:
    assert extract_bottom_cursor(user_timeline([tweet_entry(1), cursor_entry("Top", "T")])) is None
    assert extract_bottom_cursor({}) is None
    assert extract_bottom_cursor(None) is None
    assert extract_bottom_cursor([1, "a", None]) is None


def test_ignores_empty_value() -> None:
    assert extract_bottom_cursor({"a": {"cursorType": "Bottom", "value": ""}}) is None


def test_first_bottom_in_document_order() -> None:
    data = {"a": [cursor_entry("Bottom", "FIRST")], "b": [cursor_entry("Bottom", "SECOND")]}
    assert extract_bottom_cursor(data) == "FIRST"


def test_deeply_nested_does_not_recurse() -> None:
    node: Dict[str, Any] = {"cursorType": "Bottom", "value": "DEEP"}
    for _ in range(5000):
        node = {"child": node}
    assert extract_bottom_cursor(node) == "DEEP"


def test_count_content_entries() -> None:
    data = user_timeline([tweet_entry(1), tweet_entry(2), cursor_entry("Bottom", "B")])
    assert count_content_entries(data) == (1, 2)
    assert count_content_entries({"x": 1}) == (0, 0)


# --- paginate ----------------------------------------------------------------


def paged_api(pages: Dict[Optional[str], Dict[str, Any]]) -> MockAPI:
    def reply(request: httpx.Request) -> httpx.Response:
        return json_response(pages[request.url.params.get("cursor")])

    return MockAPI(reply)


def three_pages() -> Dict[Optional[str], Dict[str, Any]]:
    return {
        None: user_timeline([tweet_entry(1), cursor_entry("Top", "T"), cursor_entry("Bottom", "c1")]),
        "c1": user_timeline([tweet_entry(2), cursor_entry("Bottom", "c2")]),
        "c2": user_timeline([tweet_entry(3), cursor_entry("Bottom", "c3")]),
        # X often keeps returning a cursor with no results at the end
        "c3": user_timeline([cursor_entry("Top", "T"), cursor_entry("Bottom", "c4")]),
        "c4": user_timeline([tweet_entry(99), cursor_entry("Bottom", "c5")]),
    }


def test_paginate_follows_cursor_and_stops_on_empty_page() -> None:
    api = paged_api(three_pages())
    client = api.client()
    pages = list(client.paginate(client.users.followers, "123", count=20, max_pages=None))
    assert len(pages) == 4
    cursors = [r.url.params.get("cursor") for r in api.requests]
    assert cursors == [None, "c1", "c2", "c3"]
    assert all(r.url.params["count"] == "20" for r in api.requests)
    assert all(r.url.path == "/user/123/followers" for r in api.requests)


def test_paginate_max_pages() -> None:
    api = paged_api(three_pages())
    client = api.client()
    pages = list(client.paginate(client.users.tweets, username="jack", max_pages=2))
    assert len(pages) == 2
    assert api.requests[0].url.params["username"] == "jack"


def test_paginate_default_max_pages() -> None:
    def reply(request: httpx.Request) -> httpx.Response:
        n = int(request.url.params.get("cursor", "0"))
        return json_response(user_timeline([tweet_entry(n), cursor_entry("Bottom", str(n + 1))]))

    client = MockAPI(reply).client()
    assert len(list(client.paginate(client.search.tweets, "python"))) == 10


def test_paginate_stops_without_cursor() -> None:
    api = paged_api({None: user_timeline([tweet_entry(1)])})
    client = api.client()
    assert len(list(client.paginate(client.lists.tweets, "55"))) == 1


def test_paginate_stops_on_repeated_cursor() -> None:
    api = paged_api({
        None: user_timeline([tweet_entry(1), cursor_entry("Bottom", "a")]),
        "a": user_timeline([tweet_entry(2), cursor_entry("Bottom", "b")]),
        "b": user_timeline([tweet_entry(3), cursor_entry("Bottom", "a")]),
    })
    client = api.client()
    assert len(list(client.paginate(client.tweets.quotes, "1", max_pages=None))) == 3


def test_paginate_same_cursor_returned() -> None:
    api = paged_api({
        None: user_timeline([tweet_entry(1), cursor_entry("Bottom", "a")]),
        "a": user_timeline([tweet_entry(2), cursor_entry("Bottom", "a")]),
    })
    client = api.client()
    assert len(list(client.paginate(client.tweets.quotes, "1", max_pages=None))) == 2


def test_paginate_start_cursor() -> None:
    api = paged_api(three_pages())
    client = api.client()
    pages = list(client.paginate(client.users.followers, "123", cursor="c2", max_pages=1))
    assert len(pages) == 1
    assert api.last.url.params["cursor"] == "c2"


def test_paginate_is_lazy() -> None:
    api = paged_api(three_pages())
    client = api.client()
    it = client.paginate(client.users.followers, "123")
    assert api.requests == []
    next(it)
    assert len(api.requests) == 1


def test_paginate_invalid_max_pages() -> None:
    client = MockAPI().client()
    with pytest.raises(ValueError):
        list(client.paginate(client.users.followers, "1", max_pages=0))


async def test_async_paginate() -> None:
    api = paged_api(three_pages())
    client = api.async_client()
    pages = [p async for p in client.paginate(client.users.followers, "123", max_pages=None)]
    assert len(pages) == 4
    assert [r.url.params.get("cursor") for r in api.requests] == [None, "c1", "c2", "c3"]


async def test_async_paginate_max_pages() -> None:
    api = paged_api(three_pages())
    client = api.async_client()
    pages = [p async for p in client.paginate(client.users.followers, username="jack", max_pages=2)]
    assert len(pages) == 2
