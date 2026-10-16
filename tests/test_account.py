"""Account actions (client.account): request path and JSON body for every method, sync and
async, plus session handling, secret masking, retries and pagination."""

from __future__ import annotations

import base64
import inspect
import json
from datetime import datetime, timezone
from typing import Any, Callable, Dict

import httpx
import pytest

from twittrapi import AsyncTwittrAPI, TwittrAPI, TwittrAPIError, XSession, unwrap_client_response
from twittrapi import ServerError, APITimeoutError

from .conftest import MockAPI, json_response

COOKIE = "auth_token=secret-token; ct0=secret-csrf; twid=u%3D12"
PROXY = "http://user:secret-pass@1.2.3.4:8080"
PASSCODE = "0420"
SESSION = XSession(COOKIE, PROXY)
DM_SESSION = XSession(COOKIE, PROXY, passcode=PASSCODE)
AUTH = {"cookie": COOKIE, "proxy": PROXY}
TID = "1585841080431321088"
UID = "44196397"
PNG = b"\x89PNG\r\n\x1a\n-image-bytes"
PNG_B64 = base64.b64encode(PNG).decode()

# (call, path, body without cookie/proxy, idempotent)
CASES = [
    # tweets
    (lambda a: a.create_tweet("Hello"), "/client/create", {"text": "Hello"}),
    (
        lambda a: a.create_tweet(
            "Look",
            media_ids=[1, "2"],
            possibly_sensitive=True,
            reply_settings="only_follows",
            quote_url="https://x.com/jack/status/20",
            note_tweet=False,
        ),
        "/client/create",
        {
            "text": "Look",
            "media_ids": ["1", "2"],
            "possibly_sensitive": True,
            "conversation_control_mode": "only_follows",
            "quote_url": "https://x.com/jack/status/20",
            "is_note_tweet": False,
        },
    ),
    (lambda a: a.create_tweet("In a community", community_id=1500), "/client/create",
     {"text": "In a community", "community_id": "1500"}),
    (lambda a: a.create_tweet("Later", schedule_time=1900000000), "/client/create",
     {"text": "Later", "schedule_time": 1900000000}),
    (
        lambda a: a.create_tweet(
            "Later", schedule_time=datetime(2030, 3, 17, 17, 46, 40, tzinfo=timezone.utc)
        ),
        "/client/create",
        {"text": "Later", "schedule_time": 1900000000},
    ),
    (
        lambda a: a.create_tweet("Tabs or spaces?", poll_choices=["Tabs", "Spaces"], poll_duration_minutes=60),
        "/client/create",
        {"text": "Tabs or spaces?", "poll": {"choices": ["Tabs", "Spaces"], "duration_minutes": 60}},
    ),
    (lambda a: a.create_tweet("Poll", poll_choices=("A", "B", "C")), "/client/create",
     {"text": "Poll", "poll": {"choices": ["A", "B", "C"]}}),
    (lambda a: a.reply(TID, "Nice"), "/client/reply", {"id": TID, "text": "Nice"}),
    (
        lambda a: a.reply(int(TID), "Nice", media_ids=["5"], quote_url="https://x.com/a/status/1", possibly_sensitive=False),
        "/client/reply",
        {"id": TID, "text": "Nice", "media_ids": ["5"], "attachment_url": "https://x.com/a/status/1", "possibly_sensitive": False},
    ),
    (lambda a: a.delete_tweet(TID), "/client/deleteTweet", {"tweet_id": TID}),
    (lambda a: a.like(TID), "/client/like", {"tweet_id": TID}),
    (lambda a: a.unlike(int(TID)), "/client/unlike", {"tweet_id": TID}),
    (lambda a: a.retweet(TID), "/client/retweet", {"tweet_id": TID}),
    (lambda a: a.unretweet(TID), "/client/unretweet", {"tweet_id": TID}),
    (lambda a: a.pin(TID), "/client/pin", {"tweet_id": TID}),
    (lambda a: a.unpin(TID), "/client/unpin", {"tweet_id": TID}),
    (lambda a: a.bookmark(TID), "/client/bookmark", {"tweet_id": TID}),
    (lambda a: a.unbookmark(TID), "/client/unbookmark", {"tweet_id": TID}),
    (lambda a: a.report(TID, UID, "SpamSimpleOption"), "/client/report",
     {"tweet_id": TID, "user_id": UID, "reason": "SpamSimpleOption"}),
    (lambda a: a.scheduled_tweets(), "/client/schedule-overview", {}),
    (lambda a: a.scheduled_tweets(ascending=False), "/client/schedule-overview", {"ascending": False}),
    (lambda a: a.delete_scheduled_tweet("1790000000000000000"), "/client/schedule-delete",
     {"scheduled_tweet_id": "1790000000000000000"}),
    # users
    (lambda a: a.follow(UID), "/client/follow", {"user_id": UID}),
    (lambda a: a.follow(username="@XDevelopers"), "/client/follow", {"username": "XDevelopers"}),
    (lambda a: a.unfollow(int(UID)), "/client/unfollow", {"user_id": UID}),
    (lambda a: a.mute(username="jack"), "/client/mute", {"username": "jack"}),
    (lambda a: a.unmute(UID), "/client/unmute", {"user_id": UID}),
    (lambda a: a.block(UID), "/client/block", {"user_id": UID}),
    (lambda a: a.unblock(username="jack"), "/client/unblock", {"username": "jack"}),
    # user_id wins over username
    (lambda a: a.follow(UID, username="jack"), "/client/follow", {"user_id": UID}),
    # reads
    (lambda a: a.home_timeline(), "/client/home-timeline", {}),
    (lambda a: a.home_timeline(count=40, include_promoted_content=False), "/client/home-timeline",
     {"count": 40, "include_promoted_content": False}),
    (lambda a: a.bookmarks(), "/client/bookmarks", {}),
    (lambda a: a.bookmarks(count=50, cursor="c1"), "/client/bookmarks", {"count": 50, "cursor": "c1"}),
    (lambda a: a.likes(count=20), "/client/likes", {"count": 20}),
    (lambda a: a.likes(user_id=12, cursor="c"), "/client/likes", {"user_id": "12", "cursor": "c"}),
    (lambda a: a.blocked(count=100), "/client/blocked", {"count": 100}),
    (lambda a: a.muted(cursor="m"), "/client/muted", {"cursor": "m"}),
    (lambda a: a.followers_you_know(UID, count=10), "/client/followers-you-know", {"user_id": UID, "count": 10}),
    (lambda a: a.followers_you_know(username="jack", cursor="f"), "/client/followers-you-know",
     {"username": "jack", "cursor": "f"}),
    # media
    (lambda a: a.upload_image(PNG), "/client/media", {"media": PNG_B64}),
    (lambda a: a.upload_image(PNG_B64, media_type="image/png"), "/client/media",
     {"media": PNG_B64, "media_type": "image/png"}),
    (lambda a: a.upload_video(b"video", 12000, media_type="video/mp4"), "/client/media/video",
     {"media": base64.b64encode(b"video").decode(), "media_type": "video/mp4", "video_duration_ms": 12000}),
    (lambda a: a.media_status("1234567890"), "/client/media/status", {"media_id": "1234567890"}),
    # profile
    (lambda a: a.update_profile(description="Building things", location="Berlin"), "/client/profile",
     {"description": "Building things", "location": "Berlin"}),
    (lambda a: a.update_profile(name="Ben", url=""), "/client/profile", {"name": "Ben", "url": ""}),
    (
        lambda a: a.update_profile(birthdate={"day": 1, "month": 2, "year": 1990, "visibility": "self"}),
        "/client/profile",
        {"birthdate": {"day": 1, "month": 2, "year": 1990, "visibility": "self"}},
    ),
    (lambda a: a.update_profile(remove_birthdate=True), "/client/profile", {"birthdate": None}),
    (lambda a: a.update_profile_image(PNG), "/client/profile/image", {"media": PNG_B64}),
    (lambda a: a.update_profile_banner(PNG, media_type="image/png"), "/client/profile/banner",
     {"media": PNG_B64, "media_type": "image/png"}),
    # lists
    (lambda a: a.lists.create("API testers"), "/client/lists/create", {"name": "API testers"}),
    (lambda a: a.lists.create("Mine", description="", private=True), "/client/lists/create",
     {"name": "Mine", "description": "", "private": True}),
    (lambda a: a.lists.update(1234, name="New"), "/client/lists/update", {"list_id": "1234", "name": "New"}),
    (lambda a: a.lists.update("1234", description="d", private=False), "/client/lists/update",
     {"list_id": "1234", "description": "d", "private": False}),
    (lambda a: a.lists.delete("1234"), "/client/lists/delete", {"list_id": "1234"}),
    (lambda a: a.lists.add_member("1234", UID), "/client/lists/members/add", {"list_id": "1234", "user_id": UID}),
    (lambda a: a.lists.remove_member("1234", username="jack"), "/client/lists/members/remove",
     {"list_id": "1234", "username": "jack"}),
    # communities
    (lambda a: a.communities.create("API testers"), "/client/communities/create", {"name": "API testers"}),
    (
        lambda a: a.communities.create(
            "API testers", description="d", join_policy="Closed", invites_policy="AdminInvitesOnly", question="Why?"
        ),
        "/client/communities/create",
        {"name": "API testers", "description": "d", "joinPolicy": "Closed", "invitesPolicy": "AdminInvitesOnly", "question": "Why?"},
    ),
    (lambda a: a.communities.delete(1500, "API testers"), "/client/communities/remove",
     {"community_id": "1500", "name": "API testers"}),
    (lambda a: a.communities.join("1500"), "/client/communities/join", {"community_id": "1500"}),
    (lambda a: a.communities.leave("1500"), "/client/communities/leave", {"community_id": "1500"}),
    # drafts
    (lambda a: a.drafts.list(), "/client/drafts", {}),
    (lambda a: a.drafts.list(ascending=True), "/client/drafts", {"ascending": True}),
    (lambda a: a.drafts.create("Draft"), "/client/drafts/create", {"text": "Draft"}),
    (lambda a: a.drafts.create(media_ids=[7]), "/client/drafts/create", {"media_ids": ["7"]}),
    (lambda a: a.drafts.edit("99", "Edited", media_ids=["7"]), "/client/drafts/edit",
     {"draft_tweet_id": "99", "text": "Edited", "media_ids": ["7"]}),
    (lambda a: a.drafts.delete(99), "/client/drafts/delete", {"draft_tweet_id": "99"}),
    # direct messages (passcode from the call; DM_CASES below use the session's)
    (lambda a: a.dm.inbox(), "/client/dm/inbox", {}),
    (lambda a: a.dm.inbox(count=50, passcode="1234"), "/client/dm/inbox", {"count": 50, "passcode": "1234"}),
    (lambda a: a.dm.conversation(user_id=12, passcode="1234"), "/client/dm/conversation",
     {"user_id": "12", "passcode": "1234"}),
    (lambda a: a.dm.conversation("12:44196397", cursor="123", passcode="1234"), "/client/dm/conversation",
     {"conversation_id": "12:44196397", "cursor": "123", "passcode": "1234"}),
    (lambda a: a.dm.conversation_info(user_id="12"), "/client/dm/conversation/info", {"user_id": "12"}),
    (lambda a: a.dm.conversation_info("12:44196397"), "/client/dm/conversation/info",
     {"conversation_id": "12:44196397"}),
    (lambda a: a.dm.set_disappearing(86400, user_id=12, passcode="1234"), "/client/dm/conversation/disappearing",
     {"user_id": "12", "passcode": "1234", "ttl_seconds": 86400}),
    (lambda a: a.dm.set_disappearing(0, "12:44196397", passcode="1234"), "/client/dm/conversation/disappearing",
     {"conversation_id": "12:44196397", "passcode": "1234", "ttl_seconds": 0}),
    (lambda a: a.dm.send("Hello", user_id=12, passcode="1234"), "/client/dm/send",
     {"user_id": "12", "passcode": "1234", "text": "Hello"}),
    (lambda a: a.dm.settings(), "/client/dm/settings", {}),
    (
        lambda a: a.dm.update_settings(allow_dms_from="verified", av_calls_enabled=False, accept_calls_from_addressbook=True),
        "/client/dm/settings/update",
        {"allow_dms_from": "verified", "av_calls_enabled": False, "accept_calls_from_addressbook": True},
    ),
    (
        lambda a: a.dm.update_settings(
            dm_receipt_settings="all_enabled",
            always_allow_dms_from_subscribers=True,
            accept_calls_from_everyone=False,
            accept_calls_from_following=True,
            accept_calls_from_verified=False,
        ),
        "/client/dm/settings/update",
        {
            "dm_receipt_settings": "all_enabled",
            "always_allow_dms_from_subscribers": True,
            "accept_calls_from_everyone": False,
            "accept_calls_from_following": True,
            "accept_calls_from_verified": False,
        },
    ),
]


def _check(api: MockAPI, path: str, fields: Dict[str, Any]) -> None:
    assert len(api.requests) == 1
    req = api.last
    assert req.method == "POST"
    assert req.url.raw_path.decode() == path
    assert not req.url.params
    assert req.headers["content-type"] == "application/json"
    assert req.headers["x-api-key"] == "test-key"
    assert json.loads(req.content) == {**AUTH, **fields}


@pytest.mark.parametrize("call,path,fields", CASES)
def test_sync(api: MockAPI, call: Callable[[Any], Any], path: str, fields: Dict[str, Any]) -> None:
    assert call(api.client(session=SESSION).account) == {"ok": True}
    _check(api, path, fields)


@pytest.mark.parametrize("call,path,fields", CASES)
async def test_async(api: MockAPI, call: Callable[[Any], Any], path: str, fields: Dict[str, Any]) -> None:
    assert await call(api.async_client(session=SESSION).account) == {"ok": True}
    _check(api, path, fields)


def _all_paths() -> set:
    return {path for _, path, _ in CASES}


def test_every_route_is_covered() -> None:
    expected = {
        "/client/create", "/client/reply", "/client/deleteTweet", "/client/like", "/client/unlike",
        "/client/retweet", "/client/unretweet", "/client/follow", "/client/unfollow", "/client/pin",
        "/client/unpin", "/client/mute", "/client/unmute", "/client/block", "/client/unblock",
        "/client/bookmark", "/client/unbookmark", "/client/bookmarks", "/client/report",
        "/client/home-timeline", "/client/schedule-overview", "/client/schedule-delete",
        "/client/media", "/client/media/video", "/client/media/status", "/client/profile",
        "/client/profile/image", "/client/profile/banner", "/client/lists/create",
        "/client/lists/update", "/client/lists/delete", "/client/lists/members/add",
        "/client/lists/members/remove", "/client/communities/create", "/client/communities/remove",
        "/client/communities/join", "/client/communities/leave", "/client/drafts",
        "/client/drafts/create", "/client/drafts/edit", "/client/drafts/delete", "/client/likes",
        "/client/blocked", "/client/muted", "/client/followers-you-know", "/client/dm/inbox",
        "/client/dm/conversation", "/client/dm/conversation/info",
        "/client/dm/conversation/disappearing", "/client/dm/send", "/client/dm/settings",
        "/client/dm/settings/update",
    }
    assert _all_paths() == expected


# Passcode from the session ---------------------------------------------------

DM_CASES = [
    (lambda a: a.dm.inbox(), "/client/dm/inbox", {"passcode": PASSCODE}),
    (lambda a: a.dm.conversation(user_id=12), "/client/dm/conversation", {"user_id": "12", "passcode": PASSCODE}),
    (lambda a: a.dm.set_disappearing(60, user_id=12), "/client/dm/conversation/disappearing",
     {"user_id": "12", "passcode": PASSCODE, "ttl_seconds": 60}),
    (lambda a: a.dm.send("Hi", "12:44196397"), "/client/dm/send",
     {"conversation_id": "12:44196397", "passcode": PASSCODE, "text": "Hi"}),
    # a passcode on the call wins over the session's
    (lambda a: a.dm.send("Hi", user_id=12, passcode="9999"), "/client/dm/send",
     {"user_id": "12", "passcode": "9999", "text": "Hi"}),
    # routes without a passcode never send it
    (lambda a: a.dm.settings(), "/client/dm/settings", {}),
    (lambda a: a.dm.conversation_info(user_id=12), "/client/dm/conversation/info", {"user_id": "12"}),
    (lambda a: a.like(TID), "/client/like", {"tweet_id": TID}),
]


@pytest.mark.parametrize("call,path,fields", DM_CASES)
def test_session_passcode(api: MockAPI, call: Callable[[Any], Any], path: str, fields: Dict[str, Any]) -> None:
    call(api.client(session=DM_SESSION).account)
    _check(api, path, fields)


# Session handling -------------------------------------------------------------


def test_session_per_call(api: MockAPI) -> None:
    other = XSession("auth_token=x; ct0=y", "http://other:1")
    client = api.client(session=SESSION)
    client.account.like(TID, session=other)
    assert json.loads(api.last.content)["cookie"] == "auth_token=x; ct0=y"
    assert json.loads(api.last.content)["proxy"] == "http://other:1"


def test_session_per_call_without_client_session(api: MockAPI) -> None:
    api.client().account.like(TID, session=SESSION)
    _check(api, "/client/like", {"tweet_id": TID})


def test_no_session_raises_before_request(api: MockAPI) -> None:
    with pytest.raises(ValueError, match="X session"):
        api.client().account.like(TID)
    with pytest.raises(ValueError, match="X session"):
        api.client().account.dm.settings()
    assert api.requests == []


def test_session_must_be_xsession(api: MockAPI) -> None:
    with pytest.raises(TypeError):
        api.client(session={"cookie": COOKIE, "proxy": PROXY})
    with pytest.raises(TypeError):
        api.client().account.like(TID, session=COOKIE)
    assert api.requests == []


@pytest.mark.parametrize(
    "args,kwargs",
    [
        (("", PROXY), {}),
        (("   ", PROXY), {}),
        ((COOKIE, ""), {}),
        ((None, PROXY), {}),
        (("ct0=b", PROXY), {}),
        (("auth_token=a", PROXY), {}),
        ((COOKIE, PROXY), {"passcode": ""}),
    ],
)
def test_xsession_validation(args: Any, kwargs: Any) -> None:
    with pytest.raises(ValueError) as info:
        XSession(*args, **kwargs)
    assert "secret" not in str(info.value)


def test_xsession_is_immutable_and_comparable() -> None:
    with pytest.raises(AttributeError):
        SESSION.cookie = "x"  # type: ignore[misc]
    with pytest.raises(AttributeError):
        SESSION._cookie = "x"  # type: ignore[misc]
    assert XSession(COOKIE, PROXY) == SESSION
    assert XSession(COOKIE, PROXY, passcode="1") != SESSION
    assert hash(XSession(COOKIE, PROXY)) == hash(SESSION)
    assert SESSION.cookie == COOKIE and SESSION.proxy == PROXY and SESSION.passcode is None


# Masking -------------------------------------------------------------------------


def _no_secrets(text: str) -> None:
    for secret in ("secret-token", "secret-csrf", "secret-pass", "1.2.3.4", PASSCODE, "auth_token", "u%3D12"):
        assert secret not in text, secret


def test_session_repr_hides_secrets() -> None:
    for text in (repr(DM_SESSION), str(DM_SESSION), f"{DM_SESSION}", "%s" % (DM_SESSION,), repr([DM_SESSION])):
        _no_secrets(text)
    assert repr(SESSION) == "XSession(cookie=<hidden>, proxy=<hidden>)"
    assert repr(DM_SESSION) == "XSession(cookie=<hidden>, proxy=<hidden>, passcode=<hidden>)"


def test_client_repr_hides_session() -> None:
    for client in (TwittrAPI(api_key="k", session=DM_SESSION), AsyncTwittrAPI(api_key="k", session=DM_SESSION)):
        text = repr(client)
        _no_secrets(text)
        assert "session=XSession(cookie=<hidden>" in text
    assert "session" not in repr(TwittrAPI(api_key="k"))


def test_validation_errors_do_not_echo_secrets(api: MockAPI) -> None:
    account = api.client(session=DM_SESSION).account
    for call in (
        lambda: account.like("not-a-number"),
        lambda: account.dm.send("", user_id=12),
        lambda: account.dm.set_disappearing(5, user_id=12),
        lambda: account.create_tweet("x", poll_choices=["only one"]),
    ):
        with pytest.raises(ValueError) as info:
            call()
        _no_secrets(str(info.value))
    assert api.requests == []


# Client-side validation -------------------------------------------------------------


@pytest.mark.parametrize(
    "call,exc",
    [
        (lambda a: a.create_tweet(""), ValueError),
        (lambda a: a.create_tweet("x", reply_settings="everyone"), ValueError),
        (lambda a: a.create_tweet("x", media_ids=["1", "2", "3", "4", "5"]), ValueError),
        (lambda a: a.create_tweet("x", media_ids="123"), TypeError),
        (lambda a: a.create_tweet("x", media_ids=["abc"]), ValueError),
        (lambda a: a.create_tweet("x", community_id="abc"), ValueError),
        (lambda a: a.create_tweet("x", schedule_time=0), ValueError),
        (lambda a: a.create_tweet("x", poll_choices=["a"]), ValueError),
        (lambda a: a.create_tweet("x", poll_choices=["a", "b", "c", "d", "e"]), ValueError),
        (lambda a: a.create_tweet("x", poll_choices=["a", " "]), ValueError),
        (lambda a: a.create_tweet("x", poll_choices="ab"), TypeError),
        (lambda a: a.create_tweet("x", poll_choices=["a", "b"], poll_duration_minutes=4), ValueError),
        (lambda a: a.create_tweet("x", poll_choices=["a", "b"], poll_duration_minutes=10081), ValueError),
        (lambda a: a.create_tweet("x", poll_choices=["a", "b"], media_ids=["1"]), ValueError),
        (lambda a: a.create_tweet("x", poll_choices=["a", "b"], schedule_time=1900000000), ValueError),
        (lambda a: a.create_tweet("x", poll_duration_minutes=60), ValueError),
        (lambda a: a.create_tweet("x", possibly_sensitive="yes"), TypeError),
        (lambda a: a.reply("12a", "x"), ValueError),
        (lambda a: a.reply(TID, ""), ValueError),
        (lambda a: a.like(True), TypeError),
        (lambda a: a.report(TID, "jack", "SpamSimpleOption"), ValueError),
        (lambda a: a.report(TID, UID, "Spam"), ValueError),
        (lambda a: a.follow(), ValueError),
        (lambda a: a.follow("jack"), ValueError),
        (lambda a: a.block(username=" @ "), ValueError),
        (lambda a: a.bookmarks(count=0), ValueError),
        (lambda a: a.bookmarks(count=101), ValueError),
        (lambda a: a.home_timeline(count=0), ValueError),
        (lambda a: a.followers_you_know(), ValueError),
        (lambda a: a.upload_image(b""), ValueError),
        (lambda a: a.upload_image(" "), ValueError),
        (lambda a: a.upload_image(123), TypeError),
        (lambda a: a.upload_video(b"v", 0), ValueError),
        (lambda a: a.media_status("x"), ValueError),
        (lambda a: a.update_profile(), ValueError),
        (lambda a: a.update_profile(name=" "), ValueError),
        (lambda a: a.update_profile(birthdate={"day": 1, "month": 2}), ValueError),
        (lambda a: a.update_profile(birthdate={"day": 1, "month": 2, "year": 1990}, remove_birthdate=True), ValueError),
        (lambda a: a.lists.create(""), ValueError),
        (lambda a: a.lists.update("1"), ValueError),
        (lambda a: a.lists.update("1", name=""), ValueError),
        (lambda a: a.lists.add_member("1"), ValueError),
        (lambda a: a.communities.create(""), ValueError),
        (lambda a: a.communities.delete("1500", ""), ValueError),
        (lambda a: a.communities.join("abc"), ValueError),
        (lambda a: a.drafts.create(), ValueError),
        (lambda a: a.drafts.edit("1", " "), ValueError),
        (lambda a: a.dm.inbox(count=51), ValueError),
        (lambda a: a.dm.conversation(user_id=12), ValueError),  # no passcode
        (lambda a: a.dm.conversation(passcode="1"), ValueError),  # no conversation
        (lambda a: a.dm.conversation(user_id="jack", passcode="1"), ValueError),
        (lambda a: a.dm.send("hi", user_id=12), ValueError),  # no passcode
        (lambda a: a.dm.send(" ", user_id=12, passcode="1"), ValueError),
        (lambda a: a.dm.send("hi", user_id=12, passcode="1" * 65), ValueError),
        (lambda a: a.dm.set_disappearing(59, user_id=12, passcode="1"), ValueError),
        (lambda a: a.dm.set_disappearing(31536001, user_id=12, passcode="1"), ValueError),
        (lambda a: a.dm.update_settings(), ValueError),
        (lambda a: a.dm.update_settings(av_calls_enabled="no"), TypeError),
    ],
)
def test_client_side_validation(api: MockAPI, call: Callable[[Any], Any], exc: type) -> None:
    with pytest.raises(exc):
        call(api.client(session=SESSION).account)
    assert api.requests == []


# Simple format ------------------------------------------------------------------------


def test_simple_format_per_call(api: MockAPI) -> None:
    api.client(session=SESSION).account.bookmarks(response_format="simple")
    assert dict(api.last.url.params) == {"format": "simple"}
    assert json.loads(api.last.content) == AUTH


def test_simple_format_from_client(api: MockAPI) -> None:
    api.client(session=SESSION, response_format="simple").account.like(TID)
    assert dict(api.last.url.params) == {"format": "simple"}


# Retries ------------------------------------------------------------------------------


def test_actions_are_not_retried_on_server_error() -> None:
    api = MockAPI(json_response({"error": "boom"}, 500), json_response({"ok": True}))
    with pytest.raises(ServerError):
        api.client(session=SESSION).account.create_tweet("Hello")
    assert len(api.requests) == 1


def test_actions_are_not_retried_after_a_read_timeout() -> None:
    api = MockAPI(httpx.ReadTimeout("slow"), json_response({"ok": True}))
    with pytest.raises(APITimeoutError):
        api.client(session=SESSION).account.like(TID)
    assert len(api.requests) == 1


def test_actions_are_retried_on_429_and_connect_errors() -> None:
    api = MockAPI(
        json_response({"error": "slow down"}, 429),
        httpx.ConnectError("refused"),
        json_response({"ok": True}),
    )
    assert api.client(session=SESSION).account.like(TID) == {"ok": True}
    assert len(api.requests) == 3


async def test_async_actions_are_not_retried_on_server_error() -> None:
    api = MockAPI(json_response({"error": "boom"}, 502), json_response({"ok": True}))
    with pytest.raises(ServerError):
        await api.async_client(session=SESSION).account.dm.send("Hi", user_id=12, passcode="1")
    assert len(api.requests) == 1


def test_reads_keep_normal_retries() -> None:
    api = MockAPI(json_response({"error": "boom"}, 500), httpx.ReadTimeout("slow"), json_response({"ok": True}))
    assert api.client(session=SESSION).account.bookmarks() == {"ok": True}
    assert len(api.requests) == 3


# Pagination ---------------------------------------------------------------------------


def _wrapped(cursor: str = "") -> Dict[str, Any]:
    entries = [{"entryId": "tweet-1", "content": {"entryType": "TimelineTimelineItem"}}]
    if cursor:
        entries.append({"entryId": f"cursor-bottom-{cursor}", "content": {"cursorType": "Bottom", "value": cursor}})
    x_body = {"data": {"bookmark_timeline_v2": {"timeline": {"instructions": [
        {"type": "TimelineAddEntries", "entries": entries}
    ]}}}}
    return {"status_code": 200, "response": json.dumps(x_body)}


def test_paginate_bookmarks_reads_wrapped_response() -> None:
    api = MockAPI(json_response(_wrapped("c1")), json_response(_wrapped()))
    client = api.client(session=SESSION)
    pages = list(client.paginate(client.account.bookmarks, count=50))
    assert len(pages) == 2
    bodies = [json.loads(r.content) for r in api.requests]
    assert [b.get("cursor") for b in bodies] == [None, "c1"]
    assert all(b["count"] == 50 and b["cookie"] == COOKIE for b in bodies)


def test_paginate_dm_conversation_follows_has_more() -> None:
    api = MockAPI(
        json_response({"conversation_id": "1:2", "messages": [{"id": "9"}], "has_more": True, "cursor": "8"}),
        json_response({"conversation_id": "1:2", "messages": [{"id": "7"}], "has_more": False}),
    )
    client = api.client(session=DM_SESSION)
    pages = list(client.paginate(client.account.dm.conversation, user_id=2))
    assert len(pages) == 2
    assert [json.loads(r.content).get("cursor") for r in api.requests] == [None, "8"]


def test_unwrap_client_response() -> None:
    assert unwrap_client_response({"status_code": 200, "response": '{"a": 1}'}) == {"a": 1}
    assert unwrap_client_response({"status_code": 200, "response": "not json"}) == {
        "status_code": 200,
        "response": "not json",
    }
    assert unwrap_client_response({"data": []}) == {"data": []}
    assert unwrap_client_response(None) is None


# API surface --------------------------------------------------------------------------


def _public_methods(obj: Any) -> Dict[str, Any]:
    return {
        name: getattr(obj, name)
        for name in dir(obj)
        if not name.startswith("_") and callable(getattr(obj, name))
    }


@pytest.mark.parametrize("path", ["account", "account.lists", "account.communities", "account.drafts", "account.dm"])
def test_async_parity(path: str) -> None:
    def resolve(client: Any) -> Any:
        for part in path.split("."):
            client = getattr(client, part)
        return client

    sync_res = resolve(TwittrAPI(api_key="k"))
    async_res = resolve(AsyncTwittrAPI(api_key="k"))
    sync_methods = _public_methods(sync_res)
    async_methods = _public_methods(async_res)
    assert sync_methods.keys() == async_methods.keys()
    for name, method in async_methods.items():
        assert inspect.iscoroutinefunction(method), name
        assert inspect.signature(method) == inspect.signature(sync_methods[name]), name


def test_expected_method_names() -> None:
    a = TwittrAPI(api_key="k").account
    assert set(_public_methods(a)) == {
        "create_tweet", "reply", "delete_tweet", "like", "unlike", "retweet", "unretweet",
        "pin", "unpin", "bookmark", "unbookmark", "report", "scheduled_tweets",
        "delete_scheduled_tweet", "follow", "unfollow", "mute", "unmute", "block", "unblock",
        "home_timeline", "bookmarks", "likes", "blocked", "muted", "followers_you_know",
        "upload_image", "upload_video", "media_status", "update_profile",
        "update_profile_image", "update_profile_banner",
    }
    assert set(_public_methods(a.lists)) == {"create", "update", "delete", "add_member", "remove_member"}
    assert set(_public_methods(a.communities)) == {"create", "delete", "join", "leave"}
    assert set(_public_methods(a.drafts)) == {"list", "create", "edit", "delete"}
    assert set(_public_methods(a.dm)) == {
        "inbox", "conversation", "conversation_info", "set_disappearing", "send", "settings",
        "update_settings",
    }


def test_error_is_twittrapi_error_subclass_for_api_errors() -> None:
    api = MockAPI(json_response({"error": "This doesn't look like a valid tweetId"}, 422))
    with pytest.raises(TwittrAPIError) as info:
        api.client(session=SESSION).account.like(TID)
    _no_secrets(str(info.value))
