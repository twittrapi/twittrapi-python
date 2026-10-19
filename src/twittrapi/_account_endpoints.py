"""Request builders for the account actions (``/client/...``).

Every account action is a POST with a JSON body holding the session (``cookie`` and
``proxy``, from :class:`~twittrapi.XSession`) and the action's fields. IDs are sent as
strings, as the API expects. Actions that change something are marked non-idempotent, so the
client does not retry them after the request may have reached the API (see
``_base.can_retry_error``); reads keep the normal retries.

Field names and rules follow the API handlers; the server validates everything again.
"""

from __future__ import annotations

import base64
from datetime import datetime
from typing import Any, Dict, List, Literal, Mapping, Optional, Sequence, TypedDict, Union

from ._endpoints import ID, MAX_COUNT, EndpointRequest, _non_empty, _numeric_id, _username
from ._session import XSession

ReplySettings = Literal["only_follows", "only_verified", "only_mentioned"]
"""Who can reply: people you follow, verified accounts, or only accounts you mention."""

ReportReason = Literal[
    "SpamSimpleOption",
    "HateOrAbuseSimpleOption",
    "ChildSafetySimpleOption",
    "ViolentSpeechSimpleOption",
    "ViolentMediaSimpleOption",
    "IRBSimpleOption",
    "ImpersonationSimpleOption",
    "AdultContentSimpleOption",
    "PrivateContentSimpleOption",
    "SuicideSelfHarmSimpleOption",
    "TerrorismSimpleOption",
    "CivicIntegritySimpleOption",
]

ArticleLifecycle = Literal["draft", "published"]
"""Which of your articles to list: drafts (the default) or published ones."""

ArticleVisibility = Literal["public", "subscribers"]
"""Who can read a published article: everyone (the default) or only your subscribers."""

ArticleReplyControl = Literal["all", "community", "verified", "byinvitation"]
"""Who can reply to a published article's post: everyone (the default), your community,
verified accounts, or only accounts you mention."""

ArticleCoverCategory = Literal["DraftTweetImage", "DraftTweetGif", "AmplifyVideo"]
"""The kind of media used as an article cover: image (the default), GIF or video."""

REPLY_SETTINGS = ("only_follows", "only_verified", "only_mentioned")
REPORT_REASONS = (
    "SpamSimpleOption",
    "HateOrAbuseSimpleOption",
    "ChildSafetySimpleOption",
    "ViolentSpeechSimpleOption",
    "ViolentMediaSimpleOption",
    "IRBSimpleOption",
    "ImpersonationSimpleOption",
    "AdultContentSimpleOption",
    "PrivateContentSimpleOption",
    "SuicideSelfHarmSimpleOption",
    "TerrorismSimpleOption",
    "CivicIntegritySimpleOption",
)

ARTICLE_LIFECYCLES = ("draft", "published")
ARTICLE_VISIBILITIES = ("public", "subscribers")
ARTICLE_REPLY_CONTROLS = ("all", "community", "verified", "byinvitation")
ARTICLE_COVER_CATEGORIES = ("DraftTweetImage", "DraftTweetGif", "AmplifyVideo")

MAX_MEDIA_IDS = 4
BOOKMARK_SEARCH_MAX_LENGTH = 500
ARTICLE_TWEET_TEXT_MAX_LENGTH = 256
POLL_MIN_CHOICES = 2
POLL_MAX_CHOICES = 4
POLL_MIN_MINUTES = 5
POLL_MAX_MINUTES = 7 * 24 * 60
DM_INBOX_MAX_COUNT = 50
DM_TTL_MIN_SECONDS = 60
DM_TTL_MAX_SECONDS = 365 * 24 * 60 * 60
DM_PASSCODE_MAX_LENGTH = 64


class _BirthdateRequired(TypedDict):
    day: int
    month: int
    year: int


class Birthdate(_BirthdateRequired, total=False):
    """Birth date for :meth:`~twittrapi.resources.Account.update_profile`.

    ``visibility`` and ``year_visibility`` are ``public``, ``followers``, ``following``,
    ``mutualfollow`` or ``self``; left out, X keeps the current setting.
    """

    visibility: str
    year_visibility: str


Media = Union[bytes, bytearray, memoryview, str]
"""A media file: raw bytes (the SDK base64-encodes them) or a string that is already base64."""


# Helpers -------------------------------------------------------------------


def _session_body(session: XSession) -> Dict[str, Any]:
    if not isinstance(session, XSession):
        raise TypeError(f"session must be an XSession, got {type(session).__name__}")
    return {"cookie": session.cookie, "proxy": session.proxy}


def _post(
    path: str,
    session: XSession,
    fields: Mapping[str, Any],
    *,
    idempotent: bool = False,
) -> EndpointRequest:
    """Builds the POST. Fields that are ``None`` are left out (the API then uses its default)."""
    body = _session_body(session)
    body.update({k: v for k, v in fields.items() if v is not None})
    return EndpointRequest(path, method="POST", body=body, idempotent=idempotent)


def _read(path: str, session: XSession, fields: Mapping[str, Any]) -> EndpointRequest:
    return _post(path, session, fields, idempotent=True)


def _int(value: Optional[int], name: str, low: int, high: Optional[int] = None) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < low or (
        high is not None and value > high
    ):
        bounds = f"from {low} to {high}" if high is not None else f">= {low}"
        raise ValueError(f"{name} must be an integer {bounds}, got {value!r}")
    return value


def _bool(value: Optional[bool], name: str) -> Optional[bool]:
    if value is not None and not isinstance(value, bool):
        raise TypeError(f"{name} must be True or False, got {type(value).__name__}")
    return value


def _required_text(value: str, name: str) -> str:
    """A required string, sent unchanged (not stripped)."""
    _non_empty(value, name)
    return value


def _text(value: Optional[str], name: str) -> Optional[str]:
    """An optional string sent as is (an empty string is a real value, e.g. to clear a field)."""
    if value is not None and not isinstance(value, str):
        raise TypeError(f"{name} must be a string, got {type(value).__name__}")
    return value


def _choice(value: Optional[str], name: str, choices: Sequence[str]) -> Optional[str]:
    if value is not None and value not in choices:
        raise ValueError(f"{name} must be one of {', '.join(choices)}; got {value!r}")
    return value


def _choice_ci(value: Optional[str], name: str, choices: Sequence[str]) -> Optional[str]:
    """Like :func:`_choice`, but case-insensitive (the API accepts any case). Sent as given."""
    if value is None:
        return None
    if not isinstance(value, str) or value.lower() not in {c.lower() for c in choices}:
        raise ValueError(f"{name} must be one of {', '.join(choices)}; got {value!r}")
    return value


def _max_length(value: Optional[str], name: str, limit: int) -> Optional[str]:
    """An optional string of at most ``limit`` characters (Unicode code points)."""
    _text(value, name)
    if value is not None and len(value) > limit:
        raise ValueError(f"{name} is too long ({len(value)} characters, maximum {limit})")
    return value


def _page(count: Optional[int], cursor: Optional[str]) -> Dict[str, Any]:
    return {"count": _int(count, "count", 1, MAX_COUNT), "cursor": cursor or None}


def _media_ids(media_ids: Optional[Sequence[ID]]) -> Optional[List[str]]:
    if media_ids is None:
        return None
    if isinstance(media_ids, (str, bytes)):
        raise TypeError("media_ids must be a list of IDs, not a single string")
    ids = [_numeric_id(m, "each media id") for m in media_ids]
    if len(ids) > MAX_MEDIA_IDS:
        raise ValueError(f"media_ids allows at most {MAX_MEDIA_IDS} items, got {len(ids)}")
    return ids or None


def _media(media: Media) -> str:
    if isinstance(media, (bytes, bytearray, memoryview)):
        data = bytes(media)
        if not data:
            raise ValueError("media must not be empty")
        return base64.b64encode(data).decode("ascii")
    if isinstance(media, str):
        return _non_empty(media, "media")
    raise TypeError(f"media must be bytes or a base64 string, got {type(media).__name__}")


def _user(user_id: Optional[ID], username: Optional[str]) -> Dict[str, Any]:
    """``user_id`` (preferred) or ``username``; the API resolves the handle itself."""
    if user_id is not None and user_id != "":
        return {"user_id": _numeric_id(user_id, "user_id")}
    if username is not None:
        return {"username": _username(username)}
    raise ValueError("Provide either user_id or username.")


def _tweet(path: str, session: XSession, tweet_id: ID) -> EndpointRequest:
    return _post(path, session, {"tweet_id": _numeric_id(tweet_id, "tweet_id")})


def _unix_seconds(value: Union[int, datetime], name: str) -> int:
    if isinstance(value, datetime):
        return int(value.timestamp())
    return int(_int(value, name, 1) or 0)


# Tweets --------------------------------------------------------------------


def create_tweet(
    session: XSession,
    text: str,
    *,
    media_ids: Optional[Sequence[ID]],
    possibly_sensitive: Optional[bool],
    reply_settings: Optional[str],
    quote_url: Optional[str],
    community_id: Optional[ID],
    note_tweet: Optional[bool],
    schedule_time: Optional[Union[int, datetime]],
    poll_choices: Optional[Sequence[str]],
    poll_duration_minutes: Optional[int],
) -> EndpointRequest:
    fields: Dict[str, Any] = {
        "text": _required_text(text, "text"),
        "media_ids": _media_ids(media_ids),
        "possibly_sensitive": _bool(possibly_sensitive, "possibly_sensitive"),
        "conversation_control_mode": _choice(reply_settings, "reply_settings", REPLY_SETTINGS),
        "quote_url": _text(quote_url, "quote_url") or None,
        "community_id": (
            _numeric_id(community_id, "community_id") if community_id is not None else None
        ),
        "is_note_tweet": _bool(note_tweet, "note_tweet"),
        "schedule_time": (
            _unix_seconds(schedule_time, "schedule_time") if schedule_time is not None else None
        ),
    }
    if poll_choices is not None:
        if isinstance(poll_choices, str):
            raise TypeError("poll_choices must be a list of strings, not a single string")
        choices = list(poll_choices)
        if not POLL_MIN_CHOICES <= len(choices) <= POLL_MAX_CHOICES:
            raise ValueError(
                f"poll_choices needs {POLL_MIN_CHOICES} to {POLL_MAX_CHOICES} choices, "
                f"got {len(choices)}"
            )
        for i, choice in enumerate(choices, 1):
            if not isinstance(choice, str) or not choice.strip():
                raise ValueError(f"poll choice {i} must be a non-empty string")
        for name in ("media_ids", "quote_url", "community_id", "schedule_time"):
            if fields[name] is not None:
                raise ValueError(f"a poll cannot be combined with {name}")
        poll: Dict[str, Any] = {"choices": choices}
        minutes = _int(poll_duration_minutes, "poll_duration_minutes", POLL_MIN_MINUTES, POLL_MAX_MINUTES)
        if minutes is not None:
            poll["duration_minutes"] = minutes
        fields["poll"] = poll
    elif poll_duration_minutes is not None:
        raise ValueError("poll_duration_minutes needs poll_choices")
    return _post("/client/create", session, fields)


def reply(
    session: XSession,
    tweet_id: ID,
    text: str,
    *,
    media_ids: Optional[Sequence[ID]],
    quote_url: Optional[str],
    possibly_sensitive: Optional[bool],
) -> EndpointRequest:
    return _post(
        "/client/reply",
        session,
        {
            "id": _numeric_id(tweet_id, "tweet_id"),
            "text": _required_text(text, "text"),
            "media_ids": _media_ids(media_ids),
            "attachment_url": _text(quote_url, "quote_url") or None,
            "possibly_sensitive": _bool(possibly_sensitive, "possibly_sensitive"),
        },
    )


TWEET_ACTIONS = {
    "delete_tweet": "/client/deleteTweet",
    "like": "/client/like",
    "unlike": "/client/unlike",
    "retweet": "/client/retweet",
    "unretweet": "/client/unretweet",
    "pin": "/client/pin",
    "unpin": "/client/unpin",
    "bookmark": "/client/bookmark",
    "unbookmark": "/client/unbookmark",
}


def tweet_action(kind: str, session: XSession, tweet_id: ID) -> EndpointRequest:
    """``kind`` is a key of TWEET_ACTIONS, e.g. "like"."""
    return _tweet(TWEET_ACTIONS[kind], session, tweet_id)


def report(session: XSession, tweet_id: ID, user_id: ID, reason: str) -> EndpointRequest:
    choice = _choice(reason, "reason", REPORT_REASONS)
    if choice is None:
        raise ValueError("reason is required")
    return _post(
        "/client/report",
        session,
        {
            "tweet_id": _numeric_id(tweet_id, "tweet_id"),
            "user_id": _numeric_id(user_id, "user_id"),
            "reason": choice,
        },
    )


def scheduled_tweets(session: XSession, ascending: Optional[bool]) -> EndpointRequest:
    return _read("/client/schedule-overview", session, {"ascending": _bool(ascending, "ascending")})


def delete_scheduled_tweet(session: XSession, scheduled_tweet_id: ID) -> EndpointRequest:
    return _post(
        "/client/schedule-delete",
        session,
        {"scheduled_tweet_id": _numeric_id(scheduled_tweet_id, "scheduled_tweet_id")},
    )


# Users ---------------------------------------------------------------------


USER_ACTIONS = {
    "follow": "/client/follow",
    "unfollow": "/client/unfollow",
    "mute": "/client/mute",
    "unmute": "/client/unmute",
    "block": "/client/block",
    "unblock": "/client/unblock",
}


def user_action(
    kind: str, session: XSession, user_id: Optional[ID], username: Optional[str]
) -> EndpointRequest:
    """``kind`` is a key of USER_ACTIONS, e.g. "follow"."""
    return _post(USER_ACTIONS[kind], session, _user(user_id, username))


# Reads of your own account -------------------------------------------------


def home_timeline(
    session: XSession, count: Optional[int], include_promoted_content: Optional[bool]
) -> EndpointRequest:
    return _read(
        "/client/home-timeline",
        session,
        {
            "count": _int(count, "count", 1, MAX_COUNT),
            "include_promoted_content": _bool(include_promoted_content, "include_promoted_content"),
        },
    )


def bookmarks(session: XSession, count: Optional[int], cursor: Optional[str]) -> EndpointRequest:
    return _read("/client/bookmarks", session, _page(count, cursor))


def likes(
    session: XSession, count: Optional[int], cursor: Optional[str], user_id: Optional[ID]
) -> EndpointRequest:
    fields = _page(count, cursor)
    if user_id is not None and user_id != "":
        fields["user_id"] = _numeric_id(user_id, "user_id")
    return _read("/client/likes", session, fields)


def blocked(session: XSession, count: Optional[int], cursor: Optional[str]) -> EndpointRequest:
    return _read("/client/blocked", session, _page(count, cursor))


def muted(session: XSession, count: Optional[int], cursor: Optional[str]) -> EndpointRequest:
    return _read("/client/muted", session, _page(count, cursor))


def followers_you_know(
    session: XSession,
    user_id: Optional[ID],
    username: Optional[str],
    count: Optional[int],
    cursor: Optional[str],
) -> EndpointRequest:
    fields = _user(user_id, username)
    fields.update(_page(count, cursor))
    return _read("/client/followers-you-know", session, fields)


# Bookmark folders and bookmark search ------------------------------------


def bookmark_folders(session: XSession, cursor: Optional[str]) -> EndpointRequest:
    return _read("/client/bookmarks/folders", session, {"cursor": cursor or None})


def bookmark_folder(session: XSession, folder_id: ID, cursor: Optional[str]) -> EndpointRequest:
    return _read(
        "/client/bookmarks/folder",
        session,
        {"folder_id": _numeric_id(folder_id, "folder_id"), "cursor": cursor or None},
    )


def search_bookmarks(
    session: XSession, query: str, count: Optional[int], cursor: Optional[str]
) -> EndpointRequest:
    _required_text(query, "query")
    if len(query.strip()) > BOOKMARK_SEARCH_MAX_LENGTH:
        raise ValueError(
            f"query is too long ({len(query.strip())} characters, "
            f"maximum {BOOKMARK_SEARCH_MAX_LENGTH})"
        )
    fields: Dict[str, Any] = {"query": query}
    fields.update(_page(count, cursor))
    return _read("/client/bookmarks/search", session, fields)


# Media ---------------------------------------------------------------------


def upload_image(session: XSession, media: Media, media_type: Optional[str]) -> EndpointRequest:
    return _post(
        "/client/media",
        session,
        {"media": _media(media), "media_type": _text(media_type, "media_type") or None},
    )


def upload_video(
    session: XSession, media: Media, video_duration_ms: int, media_type: Optional[str]
) -> EndpointRequest:
    duration = _int(video_duration_ms, "video_duration_ms", 1)
    if duration is None:
        raise ValueError("video_duration_ms is required")
    return _post(
        "/client/media/video",
        session,
        {
            "media": _media(media),
            "media_type": _text(media_type, "media_type") or None,
            "video_duration_ms": duration,
        },
    )


def media_status(session: XSession, media_id: ID) -> EndpointRequest:
    return _read("/client/media/status", session, {"media_id": _numeric_id(media_id, "media_id")})


# Profile -------------------------------------------------------------------


def update_profile(
    session: XSession,
    *,
    name: Optional[str],
    description: Optional[str],
    location: Optional[str],
    url: Optional[str],
    birthdate: Optional[Birthdate],
    remove_birthdate: bool,
) -> EndpointRequest:
    fields: Dict[str, Any] = {
        "name": _text(name, "name"),
        "description": _text(description, "description"),
        "location": _text(location, "location"),
        "url": _text(url, "url"),
    }
    if name is not None and not name.strip():
        raise ValueError("name cannot be empty")
    if birthdate is not None and remove_birthdate:
        raise ValueError("Pass birthdate or remove_birthdate=True, not both.")
    if birthdate is not None:
        if not isinstance(birthdate, Mapping):
            raise TypeError("birthdate must be a dict {day, month, year, ...}")
        for key in ("day", "month", "year"):
            if key not in birthdate:
                raise ValueError(f"birthdate needs {key}")
        fields["birthdate"] = dict(birthdate)
    request = _post("/client/profile", session, fields)
    if remove_birthdate:
        assert request.body is not None
        request.body["birthdate"] = None  # null removes the birth date
    if len(request.body or {}) <= 2:
        raise ValueError(
            "Pass at least one of name, description, location, url, birthdate or remove_birthdate."
        )
    return request


def update_profile_media(
    kind: str, session: XSession, media: Media, media_type: Optional[str]
) -> EndpointRequest:
    """``kind`` is "image" (profile picture) or "banner" (header image)."""
    return _post(
        f"/client/profile/{kind}",
        session,
        {"media": _media(media), "media_type": _text(media_type, "media_type") or None},
    )


# Lists ---------------------------------------------------------------------


def list_create(
    session: XSession, name: str, description: Optional[str], private: Optional[bool]
) -> EndpointRequest:
    return _post(
        "/client/lists/create",
        session,
        {
            "name": _required_text(name, "name"),
            "description": _text(description, "description"),
            "private": _bool(private, "private"),
        },
    )


def list_update(
    session: XSession,
    list_id: ID,
    name: Optional[str],
    description: Optional[str],
    private: Optional[bool],
) -> EndpointRequest:
    if name is None and description is None and private is None:
        raise ValueError("Pass at least one of name, description or private.")
    if name is not None and not str(name).strip():
        raise ValueError("name cannot be empty")
    return _post(
        "/client/lists/update",
        session,
        {
            "list_id": _numeric_id(list_id, "list_id"),
            "name": _text(name, "name"),
            "description": _text(description, "description"),
            "private": _bool(private, "private"),
        },
    )


def list_delete(session: XSession, list_id: ID) -> EndpointRequest:
    return _post("/client/lists/delete", session, {"list_id": _numeric_id(list_id, "list_id")})


def list_member(
    op: str, session: XSession, list_id: ID, user_id: Optional[ID], username: Optional[str]
) -> EndpointRequest:
    """``op`` is "add" or "remove"."""
    fields: Dict[str, Any] = {"list_id": _numeric_id(list_id, "list_id")}
    fields.update(_user(user_id, username))
    return _post(f"/client/lists/members/{op}", session, fields)


# Communities ---------------------------------------------------------------


def community_create(
    session: XSession,
    name: str,
    description: Optional[str],
    join_policy: Optional[str],
    invites_policy: Optional[str],
    question: Optional[str],
) -> EndpointRequest:
    return _post(
        "/client/communities/create",
        session,
        {
            "name": _required_text(name, "name"),
            "description": _text(description, "description"),
            "joinPolicy": _text(join_policy, "join_policy"),
            "invitesPolicy": _text(invites_policy, "invites_policy"),
            "question": _text(question, "question"),
        },
    )


def community_delete(session: XSession, community_id: ID, name: str) -> EndpointRequest:
    return _post(
        "/client/communities/remove",
        session,
        {
            "community_id": _numeric_id(community_id, "community_id"),
            "name": _required_text(name, "name"),
        },
    )


def community_membership(op: str, session: XSession, community_id: ID) -> EndpointRequest:
    """``op`` is "join" or "leave"."""
    return _post(
        f"/client/communities/{op}",
        session,
        {"community_id": _numeric_id(community_id, "community_id")},
    )


def community_memberships(session: XSession, cursor: Optional[str]) -> EndpointRequest:
    return _read("/client/communities/memberships", session, {"cursor": cursor or None})


# Drafts --------------------------------------------------------------------


def drafts(session: XSession, ascending: Optional[bool]) -> EndpointRequest:
    return _read("/client/drafts", session, {"ascending": _bool(ascending, "ascending")})


def _draft_fields(text: Optional[str], media_ids: Optional[Sequence[ID]]) -> Dict[str, Any]:
    fields = {"text": _text(text, "text"), "media_ids": _media_ids(media_ids)}
    if (text is None or not text.strip()) and fields["media_ids"] is None:
        raise ValueError("Pass text or media_ids.")
    return fields


def draft_create(
    session: XSession, text: Optional[str], media_ids: Optional[Sequence[ID]]
) -> EndpointRequest:
    return _post("/client/drafts/create", session, _draft_fields(text, media_ids))


def draft_edit(
    session: XSession, draft_id: ID, text: Optional[str], media_ids: Optional[Sequence[ID]]
) -> EndpointRequest:
    fields: Dict[str, Any] = {"draft_tweet_id": _numeric_id(draft_id, "draft_id")}
    fields.update(_draft_fields(text, media_ids))
    return _post("/client/drafts/edit", session, fields)


def draft_delete(session: XSession, draft_id: ID) -> EndpointRequest:
    return _post(
        "/client/drafts/delete", session, {"draft_tweet_id": _numeric_id(draft_id, "draft_id")}
    )


# Articles ------------------------------------------------------------------


def articles(
    session: XSession,
    lifecycle: Optional[str],
    count: Optional[int],
    cursor: Optional[str],
    user_id: Optional[ID],
) -> EndpointRequest:
    fields: Dict[str, Any] = {"lifecycle": _choice_ci(lifecycle, "lifecycle", ARTICLE_LIFECYCLES)}
    fields.update(_page(count, cursor))
    if user_id is not None and user_id != "":
        fields["user_id"] = _numeric_id(user_id, "user_id")
    return _read("/client/articles", session, fields)


def article_get(session: XSession, article_id: ID) -> EndpointRequest:
    return _read(
        "/client/articles/get", session, {"article_id": _numeric_id(article_id, "article_id")}
    )


def _content_state(value: Optional[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise TypeError('content_state must be a dict {"blocks": [...], "entity_map": [...]}')
    if not isinstance(value.get("blocks"), list):
        raise ValueError('content_state needs "blocks" (a list)')
    if "entity_map" in value and not isinstance(value["entity_map"], list):
        raise ValueError('content_state "entity_map" must be a list')
    return dict(value)


def _article_content(
    title: Optional[str], text: Optional[str], content_state: Optional[Mapping[str, Any]]
) -> Dict[str, Any]:
    if text is not None and content_state is not None:
        raise ValueError("Pass text or content_state, not both.")
    return {
        "title": _text(title, "title"),
        "text": _text(text, "text"),
        "content_state": _content_state(content_state),
    }


def article_create(
    session: XSession,
    title: Optional[str],
    text: Optional[str],
    content_state: Optional[Mapping[str, Any]],
) -> EndpointRequest:
    return _post("/client/articles/create", session, _article_content(title, text, content_state))


def article_update(
    session: XSession,
    article_id: ID,
    *,
    title: Optional[str],
    text: Optional[str],
    content_state: Optional[Mapping[str, Any]],
    cover_media_id: Optional[ID],
    cover_media_category: Optional[str],
    remove_cover: bool,
) -> EndpointRequest:
    fields: Dict[str, Any] = {"article_id": _numeric_id(article_id, "article_id")}
    fields.update(_article_content(title, text, content_state))
    _bool(remove_cover, "remove_cover")
    if cover_media_id is not None and remove_cover:
        raise ValueError("Pass cover_media_id or remove_cover=True, not both.")
    if cover_media_category is not None and cover_media_id is None:
        raise ValueError("cover_media_category needs cover_media_id")
    if cover_media_id is not None:
        fields["cover_media_id"] = _numeric_id(cover_media_id, "cover_media_id")
        fields["cover_media_category"] = _choice_ci(
            cover_media_category, "cover_media_category", ARTICLE_COVER_CATEGORIES
        )
    if remove_cover:
        fields["remove_cover"] = True
    if all(fields[k] is None for k in ("title", "text", "content_state")) and not (
        cover_media_id is not None or remove_cover
    ):
        raise ValueError(
            "Pass at least one of title, text, content_state, cover_media_id or "
            "remove_cover=True."
        )
    return _post("/client/articles/update", session, fields)


def article_publish(
    session: XSession,
    article_id: ID,
    visibility: Optional[str],
    reply_control: Optional[str],
    tweet_text: Optional[str],
) -> EndpointRequest:
    return _post(
        "/client/articles/publish",
        session,
        {
            "article_id": _numeric_id(article_id, "article_id"),
            "visibility": _choice_ci(visibility, "visibility", ARTICLE_VISIBILITIES),
            "reply_control": _choice_ci(reply_control, "reply_control", ARTICLE_REPLY_CONTROLS),
            "tweet_text": _max_length(tweet_text, "tweet_text", ARTICLE_TWEET_TEXT_MAX_LENGTH),
        },
    )


def article_action(op: str, session: XSession, article_id: ID) -> EndpointRequest:
    """``op`` is "unpublish" or "delete"."""
    return _post(
        f"/client/articles/{op}", session, {"article_id": _numeric_id(article_id, "article_id")}
    )


# Direct messages -----------------------------------------------------------


def _passcode(
    session: XSession, passcode: Optional[str], required: bool
) -> Optional[str]:
    value = passcode if passcode is not None else session.passcode
    if value is not None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("passcode must be a non-empty string")
        if len(value) > DM_PASSCODE_MAX_LENGTH:
            raise ValueError(f"passcode is longer than {DM_PASSCODE_MAX_LENGTH} characters")
    elif required:
        raise ValueError(
            "This call needs your X Chat passcode: pass passcode=... or "
            "XSession(..., passcode=...)."
        )
    return value


def _conversation(conversation_id: Optional[str], user_id: Optional[ID]) -> Dict[str, Any]:
    if conversation_id is not None and conversation_id != "":
        return {"conversation_id": _non_empty(conversation_id, "conversation_id")}
    if user_id is not None and user_id != "":
        return {"user_id": _numeric_id(user_id, "user_id")}
    raise ValueError("Provide either conversation_id or user_id.")


def dm_inbox(session: XSession, count: Optional[int], passcode: Optional[str]) -> EndpointRequest:
    return _read(
        "/client/dm/inbox",
        session,
        {
            "passcode": _passcode(session, passcode, required=False),
            "count": _int(count, "count", 1, DM_INBOX_MAX_COUNT),
        },
    )


def dm_conversation(
    session: XSession,
    conversation_id: Optional[str],
    user_id: Optional[ID],
    cursor: Optional[str],
    passcode: Optional[str],
) -> EndpointRequest:
    fields = _conversation(conversation_id, user_id)
    fields["passcode"] = _passcode(session, passcode, required=True)
    fields["cursor"] = cursor or None
    return _read("/client/dm/conversation", session, fields)


def dm_conversation_info(
    session: XSession, conversation_id: Optional[str], user_id: Optional[ID]
) -> EndpointRequest:
    return _read("/client/dm/conversation/info", session, _conversation(conversation_id, user_id))


def dm_set_disappearing(
    session: XSession,
    ttl_seconds: int,
    conversation_id: Optional[str],
    user_id: Optional[ID],
    passcode: Optional[str],
) -> EndpointRequest:
    if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int) or (
        ttl_seconds != 0 and not DM_TTL_MIN_SECONDS <= ttl_seconds <= DM_TTL_MAX_SECONDS
    ):
        raise ValueError(
            f"ttl_seconds must be 0 (off) or from {DM_TTL_MIN_SECONDS} to {DM_TTL_MAX_SECONDS}, "
            f"got {ttl_seconds!r}"
        )
    fields = _conversation(conversation_id, user_id)
    fields["passcode"] = _passcode(session, passcode, required=True)
    fields["ttl_seconds"] = ttl_seconds
    return _post("/client/dm/conversation/disappearing", session, fields)


def dm_send(
    session: XSession,
    text: str,
    conversation_id: Optional[str],
    user_id: Optional[ID],
    passcode: Optional[str],
) -> EndpointRequest:
    _required_text(text, "text")
    fields = _conversation(conversation_id, user_id)
    fields["passcode"] = _passcode(session, passcode, required=True)
    fields["text"] = text
    return _post("/client/dm/send", session, fields)


def dm_settings(session: XSession) -> EndpointRequest:
    return _read("/client/dm/settings", session, {})


def dm_update_settings(
    session: XSession,
    *,
    allow_dms_from: Optional[str],
    dm_receipt_settings: Optional[str],
    always_allow_dms_from_subscribers: Optional[bool],
    av_calls_enabled: Optional[bool],
    accept_calls_from_everyone: Optional[bool],
    accept_calls_from_following: Optional[bool],
    accept_calls_from_verified: Optional[bool],
    accept_calls_from_addressbook: Optional[bool],
) -> EndpointRequest:
    fields: Dict[str, Any] = {
        "allow_dms_from": _text(allow_dms_from, "allow_dms_from"),
        "dm_receipt_settings": _text(dm_receipt_settings, "dm_receipt_settings"),
    }
    flags = {
        "always_allow_dms_from_subscribers": always_allow_dms_from_subscribers,
        "av_calls_enabled": av_calls_enabled,
        "accept_calls_from_everyone": accept_calls_from_everyone,
        "accept_calls_from_following": accept_calls_from_following,
        "accept_calls_from_verified": accept_calls_from_verified,
        "accept_calls_from_addressbook": accept_calls_from_addressbook,
    }
    for key, value in flags.items():
        fields[key] = _bool(value, key)
    if all(v is None for v in fields.values()):
        raise ValueError("Pass at least one setting to change.")
    return _post("/client/dm/settings/update", session, fields)
