"""The opt-in simple response format (``format=simple``).

Fixtures in tests/fixtures/simple are the API's simple-format output for real captured
responses, copied from the backend's normalize testdata (twitter-ts,
go/internal/normalize/testdata/simple). No network access.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any, Callable, Dict, List

import pytest

from twittrapi import AsyncTwittrAPI, TwittrAPI, simple_next_cursor
from twittrapi.models import (
    Page,
    Tweet,
    UnavailableTweet,
    User,
    UserRef,
    parse_tweet,
    tweets_page,
    users_page,
)
from twittrapi.pagination import is_simple_page

from .conftest import MockAPI, json_response
from .test_resources import CASES, TID, UID

SIMPLE = Path(__file__).parent / "fixtures" / "simple"


def simple(name: str) -> Any:
    return json.loads((SIMPLE / f"{name}.json").read_text(encoding="utf-8"))


def query(api: MockAPI, index: int = -1) -> Dict[str, str]:
    return dict(api.requests[index].url.params)


# --- client configuration ------------------------------------------------------


def test_default_is_raw_and_sends_no_format_param(api: MockAPI) -> None:
    client = api.client()
    assert client.response_format == "raw"
    client.users.get_by_username("jack")
    assert "format" not in query(api)


def test_client_level_simple_sends_format_param(api: MockAPI) -> None:
    client = api.client(response_format="simple")
    assert client.response_format == "simple"
    client.users.tweets(UID, count=20)
    assert query(api) == {"count": "20", "format": "simple"}
    assert "simple" in repr(client)


@pytest.mark.parametrize("bad", ["Simple", "json", "", None, 1])
def test_invalid_client_format(bad: Any) -> None:
    with pytest.raises(ValueError, match="response_format"):
        TwittrAPI(api_key="k", response_format=bad)
    with pytest.raises(ValueError, match="response_format"):
        AsyncTwittrAPI(api_key="k", response_format=bad)


def test_invalid_per_call_format(api: MockAPI) -> None:
    client = api.client()
    with pytest.raises(ValueError, match="response_format"):
        client.users.get_by_id(UID, response_format="compact")  # type: ignore[arg-type]
    assert api.requests == []


# --- per-call override -----------------------------------------------------------


def test_per_call_simple_on_raw_client(api: MockAPI) -> None:
    client = api.client()
    client.tweets.get(TID, response_format="simple")
    assert query(api) == {"format": "simple"}
    client.tweets.get(TID)
    assert query(api) == {}


def test_per_call_raw_on_simple_client(api: MockAPI) -> None:
    client = api.client(response_format="simple")
    client.search.tweets("python", count=10, response_format="raw")
    assert query(api) == {"searchItem": "python", "count": "10"}
    client.search.tweets("python", count=10)
    assert query(api)["format"] == "simple"


async def test_async_per_call_override(api: MockAPI) -> None:
    client = api.async_client()
    await client.users.followers(username="jack", response_format="simple")
    assert query(api) == {"username": "jack", "format": "simple"}
    await client.users.followers(username="jack")
    assert query(api) == {"username": "jack"}


@pytest.mark.parametrize("call,path,params", CASES)
def test_every_method_sends_format_simple(
    api: MockAPI, call: Callable[[Any], Any], path: str, params: Dict[str, str]
) -> None:
    call(api.client(response_format="simple"))
    assert api.last.url.raw_path.decode().split("?")[0] == path
    assert query(api) == {**params, "format": "simple"}


@pytest.mark.parametrize("call,path,params", CASES)
async def test_every_async_method_sends_format_simple(
    api: MockAPI, call: Callable[[Any], Any], path: str, params: Dict[str, str]
) -> None:
    await call(api.async_client(response_format="simple"))
    assert api.last.url.raw_path.decode().split("?")[0] == path
    assert query(api) == {**params, "format": "simple"}


@pytest.mark.parametrize("client_cls", [TwittrAPI, AsyncTwittrAPI])
def test_every_method_accepts_response_format(client_cls: Any) -> None:
    client = client_cls(api_key="k")
    names = ["users", "tweets", "search", "lists", "communities", "trends"]
    checked = 0
    for name in names:
        resource = getattr(client, name)
        for attr, method in inspect.getmembers(resource, inspect.ismethod):
            if attr.startswith("_"):
                continue
            param = inspect.signature(method).parameters.get("response_format")
            assert param is not None, f"{name}.{attr} has no response_format"
            assert param.kind is inspect.Parameter.KEYWORD_ONLY
            assert param.default is None
            checked += 1
    assert checked == 23


# --- models ----------------------------------------------------------------------


def test_parse_user() -> None:
    user = User.from_dict(simple("user-by-username-username")["data"])
    assert user.id == "2244994945"
    assert user.username == "XDevelopers"
    assert user.verified is True
    assert user.verified_type == "Business"
    assert user.created_at == "2013-12-14T04:35:55Z"
    assert user.counts.followers == 698074
    assert user.counts.listed == 2977
    assert user.pinned_tweet_ids == ["2019881223666233717"]
    assert user.is_automated is False


def test_parse_single_tweet() -> None:
    tweet = parse_tweet(simple("simpletweet-tweetid")["data"])
    assert isinstance(tweet, Tweet)
    assert tweet.id and tweet.url.endswith(tweet.id)
    assert isinstance(tweet.author, User)
    assert tweet.counts.likes >= 0


def test_parse_tweets_page() -> None:
    body = simple("user-userid-tweets")
    page = tweets_page(body)
    assert isinstance(page, Page)
    assert page.has_next_page is True
    assert page.next_cursor == body["nextCursor"]
    assert page.previous_cursor == body["previousCursor"]
    (tweet,) = page.data
    assert isinstance(tweet, Tweet)
    assert tweet.id == "2019881223666233717"
    assert tweet.created_at == "2026-02-06T21:09:45Z"
    assert tweet.lang == "en"
    assert tweet.is_pinned is True
    assert tweet.author is not None and tweet.author.username == "XDevelopers"
    assert tweet.urls == ["http://developer.x.com"]
    assert tweet.counts.views is not None


def test_parse_quoted_retweet_media_and_unavailable() -> None:
    page = tweets_page(simple("capture-user_tweets"))
    tweets = {t.id: t for t in page.data}

    quoting = tweets["2107953725071626260"]
    assert isinstance(quoting, Tweet) and isinstance(quoting.quoted, Tweet)
    assert quoting.quoted.author is not None and quoting.quoted.author.username == "bot"
    (video,) = quoting.quoted.media
    assert video.type == "video"
    assert video.preview_url.startswith("https://")
    assert video.duration_ms == 12166 and video.alt_text is None

    retweet = tweets["2108968360692404261"]
    assert isinstance(retweet, Tweet) and isinstance(retweet.retweet_of, Tweet)
    assert retweet.text.startswith("RT @")

    with_gone_quote = tweets["2107953012975235537"]
    assert isinstance(with_gone_quote, Tweet)
    assert isinstance(with_gone_quote.retweet_of, Tweet)
    assert with_gone_quote.quoted == UnavailableTweet(id="2107952086193508716")


def test_parse_unavailable_list_item() -> None:
    item = parse_tweet({"id": "1", "unavailable": True})
    assert item == UnavailableTweet(id="1")


def test_parse_article() -> None:
    page = tweets_page(simple("user-userid-articles"))
    tweet = page.data[0]
    assert isinstance(tweet, Tweet) and tweet.article is not None
    assert tweet.article.id == "2041225663047151616"
    assert tweet.article.title.startswith("X API Major Upgrades")


def test_parse_users_page_and_last_page() -> None:
    page = users_page(simple("user-userid-followers"))
    assert [u.id for u in page.data] == ["1000000000000000001", "1000000000000000002"]
    assert page.has_next_page is True and page.next_cursor
    assert page.previous_cursor is None

    last = users_page(simple("tweet-tweetid-favorites"))
    assert last.data == [] and last.has_next_page is False and last.next_cursor is None


def test_models_are_lenient() -> None:
    tweet = Tweet.from_dict({"id": "5", "newField": 1, "counts": None, "media": None})
    assert tweet.id == "5" and tweet.counts.likes == 0 and tweet.media == []
    assert tweet.author is None and tweet.quoted is None
    ref = UserRef.from_dict({"id": "1", "username": "a"})
    assert ref == UserRef(id="1", username="a")


def test_page_rejects_raw_body() -> None:
    with pytest.raises(TypeError, match="simple"):
        tweets_page({"data": {"user": {"result": {}}}})


# --- pagination ------------------------------------------------------------------


def test_simple_next_cursor() -> None:
    body = simple("user-userid-tweets")
    assert is_simple_page(body)
    assert simple_next_cursor(body) == body["nextCursor"]
    assert simple_next_cursor({**body, "hasNextPage": False}) is None
    assert simple_next_cursor(simple("tweet-tweetid-favorites")) is None
    assert simple_next_cursor(simple("user-by-username-username")) is None
    assert not is_simple_page(simple("user-by-username-username"))


def last_page() -> Any:
    return simple("tweet-tweetid-favorites")


def test_paginate_follows_next_cursor_until_has_next_page_false() -> None:
    first = simple("user-userid-followers")
    api = MockAPI(json_response(first), json_response(last_page()))
    client = api.client(response_format="simple")
    pages = list(client.paginate(client.users.followers, UID, count=20))
    assert len(pages) == 2
    assert query(api, 0) == {"count": "20", "format": "simple"}
    assert query(api, 1) == {"count": "20", "cursor": first["nextCursor"], "format": "simple"}


def test_paginate_stops_when_has_next_page_false_even_with_cursor() -> None:
    body = {**simple("user-userid-tweets"), "hasNextPage": False}
    api = MockAPI(json_response(body))
    client = api.client(response_format="simple")
    assert len(list(client.paginate(client.users.tweets, UID))) == 1
    assert len(api.requests) == 1


def test_paginate_simple_per_call_on_raw_client() -> None:
    first = simple("user-userid-tweets")
    api = MockAPI(json_response(first), json_response(last_page()))
    client = api.client()
    pages = list(
        client.paginate(client.users.tweets, username="jack", response_format="simple")
    )
    assert len(pages) == 2
    assert all(dict(r.url.params)["format"] == "simple" for r in api.requests)
    assert dict(api.requests[1].url.params)["cursor"] == first["nextCursor"]


def test_paginate_simple_three_pages_with_max_pages() -> None:
    def page(n: int) -> Dict[str, Any]:
        return {"data": [{"id": str(n)}], "nextCursor": f"c{n}", "previousCursor": None,
                "hasNextPage": True}

    api = MockAPI(*(json_response(page(n)) for n in range(1, 10)))
    client = api.client(response_format="simple")
    pages = list(client.paginate(client.search.tweets, "x", max_pages=3))
    assert [p["data"][0]["id"] for p in pages] == ["1", "2", "3"]
    assert [dict(r.url.params).get("cursor") for r in api.requests] == [None, "c1", "c2"]


def test_paginate_simple_stops_on_repeated_cursor() -> None:
    body = {"data": [{"id": "1"}], "nextCursor": "same", "previousCursor": None, "hasNextPage": True}
    api = MockAPI(json_response(body))
    client = api.client(response_format="simple")
    assert len(list(client.paginate(client.users.tweets, UID, max_pages=None))) == 2


def test_paginate_simple_falls_back_to_raw_cursor_for_raw_body() -> None:
    # Routes without a simple format answer raw; the X bottom cursor is still followed.
    from .test_pagination import cursor_entry, tweet_entry, user_timeline

    raw = user_timeline([tweet_entry(1), cursor_entry("Bottom", "RAWCURSOR")])
    api = MockAPI(json_response(raw), json_response(last_page()))
    client = api.client(response_format="simple")
    pages = list(client.paginate(client.users.tweets, UID))
    assert len(pages) == 2
    assert dict(api.requests[1].url.params)["cursor"] == "RAWCURSOR"


def test_raw_pagination_unchanged_by_default() -> None:
    from .test_pagination import cursor_entry, tweet_entry, user_timeline

    pages_data: List[Any] = [
        user_timeline([tweet_entry(1), cursor_entry("Bottom", "B1")]),
        user_timeline([cursor_entry("Bottom", "B2")]),
    ]
    api = MockAPI(*(json_response(p) for p in pages_data))
    client = api.client()
    assert len(list(client.paginate(client.users.tweets, UID))) == 2
    assert all("format" not in dict(r.url.params) for r in api.requests)


async def test_async_paginate_simple() -> None:
    first = simple("user-userid-followers")
    api = MockAPI(json_response(first), json_response(last_page()))
    client = api.async_client(response_format="simple")
    pages = [p async for p in client.paginate(client.users.followers, UID)]
    assert len(pages) == 2
    assert dict(api.requests[1].url.params)["cursor"] == first["nextCursor"]
