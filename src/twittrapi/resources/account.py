"""Account actions with your own X session: ``client.account``.

Every method sends a POST to ``/client/...`` with the session's cookie and proxy in the JSON
body. The session comes from ``session=`` on the call or from the client. See
:class:`Account` and https://twittrapi.com/docs/x-session.

The async classes are generated from the sync ones (same methods and signatures).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Mapping, Optional, Sequence, Union

from .. import _account_endpoints as A
from .._account_endpoints import (
    ArticleCoverCategory,
    ArticleLifecycle,
    ArticleReplyControl,
    ArticleVisibility,
    Birthdate,
    Media,
    ReplySettings,
    ReportReason,
)
from .._base import ResponseFormat
from .._endpoints import ID
from .._session import XSession
from ._base import AsyncResource, SyncResource

if TYPE_CHECKING:
    from .._client import AsyncTwittrAPI, TwittrAPI

__all__ = [
    "Account",
    "AccountLists",
    "AccountCommunities",
    "AccountDrafts",
    "AccountArticles",
    "AccountDM",
    "AsyncAccount",
    "AsyncAccountLists",
    "AsyncAccountCommunities",
    "AsyncAccountDrafts",
    "AsyncAccountArticles",
    "AsyncAccountDM",
]


class AccountLists(SyncResource):
    """Create, change and delete your lists, and add or remove members.
    ``client.account.lists``."""

    def create(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        private: Optional[bool] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Create a list. ``name`` up to 25 characters, ``description`` up to 100;
        ``private=True`` makes it visible only to you."""
        return self._post(
            A.list_create(self._session(session), name, description, private), response_format
        )

    def update(
        self,
        list_id: ID,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        private: Optional[bool] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Change a list's name, description or visibility. Pass at least one; the others
        stay as they are."""
        return self._post(
            A.list_update(self._session(session), list_id, name, description, private),
            response_format,
        )

    def delete(
        self,
        list_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Delete one of your lists."""
        return self._post(A.list_delete(self._session(session), list_id), response_format)

    def add_member(
        self,
        list_id: ID,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Add an account (``user_id`` or ``username``) to one of your lists."""
        return self._post(
            A.list_member("add", self._session(session), list_id, user_id, username),
            response_format,
        )

    def remove_member(
        self,
        list_id: ID,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Remove an account (``user_id`` or ``username``) from one of your lists."""
        return self._post(
            A.list_member("remove", self._session(session), list_id, user_id, username),
            response_format,
        )


class AccountCommunities(SyncResource):
    """Create, delete, join and leave communities, and list the ones you belong to.
    ``client.account.communities``."""

    def create(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        join_policy: Optional[str] = None,
        invites_policy: Optional[str] = None,
        question: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Create a community owned by your account.

        ``join_policy`` (default ``"Open"``) and ``invites_policy`` (default
        ``"MemberInvitesAllowed"``) are passed to X as is. ``question`` is asked of people
        who request to join.
        """
        return self._post(
            A.community_create(
                self._session(session), name, description, join_policy, invites_policy, question
            ),
            response_format,
        )

    def delete(
        self,
        community_id: ID,
        name: str,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Delete a community you own. X wants its ``name`` together with the ID."""
        return self._post(
            A.community_delete(self._session(session), community_id, name), response_format
        )

    def join(
        self,
        community_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Join a community."""
        return self._post(
            A.community_membership("join", self._session(session), community_id),
            response_format,
        )

    def leave(
        self,
        community_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Leave a community."""
        return self._post(
            A.community_membership("leave", self._session(session), community_id),
            response_format,
        )

    def memberships(
        self,
        *,
        cursor: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Communities your account belongs to. Paginated."""
        return self._post(
            A.community_memberships(self._session(session), cursor), response_format
        )


class AccountDrafts(SyncResource):
    """Your unsent tweet drafts. ``client.account.drafts``."""

    def list(
        self,
        *,
        ascending: Optional[bool] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Your drafts. Newest first unless ``ascending=True``."""
        return self._post(A.drafts(self._session(session), ascending), response_format)

    def create(
        self,
        text: Optional[str] = None,
        *,
        media_ids: Optional[Sequence[ID]] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Save a draft. Needs ``text`` or ``media_ids`` (up to 4)."""
        return self._post(
            A.draft_create(self._session(session), text, media_ids), response_format
        )

    def edit(
        self,
        draft_id: ID,
        text: Optional[str] = None,
        *,
        media_ids: Optional[Sequence[ID]] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Replace a draft's text and media. Needs ``text`` or ``media_ids``."""
        return self._post(
            A.draft_edit(self._session(session), draft_id, text, media_ids), response_format
        )

    def delete(
        self,
        draft_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Delete a draft."""
        return self._post(A.draft_delete(self._session(session), draft_id), response_format)


class AccountArticles(SyncResource):
    """Your long-form X Articles: list, read, write, publish and delete them.
    ``client.account.articles``.

    Needs X Premium: X offers Articles only to Premium accounts. Content is either plain
    ``text`` (one paragraph per line) or ``content_state``, X's own format
    (``{"blocks": [...], "entity_map": [...]}``, as :meth:`get` returns it).
    """

    def list(
        self,
        *,
        lifecycle: Optional[ArticleLifecycle] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        user_id: Optional[ID] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Your articles: ``lifecycle="draft"`` (default) or ``"published"``. Paginated.
        Needs X Premium.

        Reads the session's account (from ``twid`` in the cookie); pass your own numeric
        ``user_id`` only if the cookie has no ``twid``.
        """
        return self._post(
            A.articles(self._session(session), lifecycle, count, cursor, user_id),
            response_format,
        )

    def get(
        self,
        article_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """One of your articles: title, ``content_state``, cover, state and metadata.
        Needs X Premium."""
        return self._post(A.article_get(self._session(session), article_id), response_format)

    def create(
        self,
        *,
        title: Optional[str] = None,
        text: Optional[str] = None,
        content_state: Optional[Mapping[str, Any]] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Create a draft article. Needs X Premium.

        Everything is optional (without it the draft starts empty). Pass ``text`` or
        ``content_state``, not both. The answer holds the new draft and its ID.
        """
        return self._post(
            A.article_create(self._session(session), title, text, content_state),
            response_format,
        )

    def update(
        self,
        article_id: ID,
        *,
        title: Optional[str] = None,
        text: Optional[str] = None,
        content_state: Optional[Mapping[str, Any]] = None,
        cover_media_id: Optional[ID] = None,
        cover_media_category: Optional[ArticleCoverCategory] = None,
        remove_cover: bool = False,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Change an article's title, content or cover. Needs X Premium.

        ``text`` or ``content_state`` (not both) replaces the whole content.
        ``cover_media_id`` comes from :meth:`Account.upload_image` or
        :meth:`Account.upload_video`; ``cover_media_category`` is ``"DraftTweetImage"``
        (default), ``"DraftTweetGif"`` or ``"AmplifyVideo"``. ``remove_cover=True`` removes
        the cover (not together with ``cover_media_id``). Pass at least one change.
        """
        return self._post(
            A.article_update(
                self._session(session),
                article_id,
                title=title,
                text=text,
                content_state=content_state,
                cover_media_id=cover_media_id,
                cover_media_category=cover_media_category,
                remove_cover=remove_cover,
            ),
            response_format,
        )

    def publish(
        self,
        article_id: ID,
        *,
        visibility: Optional[ArticleVisibility] = None,
        reply_control: Optional[ArticleReplyControl] = None,
        tweet_text: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Publish a draft article as a post. Needs X Premium.

        ``visibility`` is ``"public"`` (default) or ``"subscribers"``. ``reply_control``
        (``"all"``, default, ``"community"``, ``"verified"`` or ``"byinvitation"``) is
        ignored for subscriber-only articles. ``tweet_text`` (up to 256 characters) is the
        text of the post that shares the article.
        """
        return self._post(
            A.article_publish(
                self._session(session), article_id, visibility, reply_control, tweet_text
            ),
            response_format,
        )

    def unpublish(
        self,
        article_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Turn a published article back into a draft. Needs X Premium."""
        return self._post(
            A.article_action("unpublish", self._session(session), article_id), response_format
        )

    def delete(
        self,
        article_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Delete an article. Needs X Premium."""
        return self._post(
            A.article_action("delete", self._session(session), article_id), response_format
        )


class AccountDM(SyncResource):
    """Your direct messages (X Chat, end-to-end encrypted). ``client.account.dm``.

    Reading and sending messages needs your X Chat passcode: set it once with
    ``XSession(..., passcode="...")`` or pass ``passcode=`` per call. It unlocks your chat
    keys for the request and is not stored by the API. Listing conversations without
    messages, conversation details and the DM settings work without it. The session cookie
    must contain ``twid``.

    Conversations are picked by ``conversation_id`` (from :meth:`inbox`) or, for a
    one-to-one chat, by the other person's numeric ``user_id``.
    """

    def inbox(
        self,
        *,
        count: Optional[int] = None,
        passcode: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Your conversations (``count`` 1 to 50, default 20), with participants and
        settings. With a passcode each one also carries its latest messages, decrypted."""
        s = self._session(session)
        return self._post(A.dm_inbox(s, count, passcode), response_format)

    def conversation(
        self,
        conversation_id: Optional[str] = None,
        *,
        user_id: Optional[ID] = None,
        cursor: Optional[str] = None,
        passcode: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Messages of one conversation, decrypted, newest first. Paginated: pass the
        ``cursor`` of the previous page for older messages. Needs the passcode."""
        s = self._session(session)
        return self._post(
            A.dm_conversation(s, conversation_id, user_id, cursor, passcode), response_format
        )

    def conversation_info(
        self,
        conversation_id: Optional[str] = None,
        *,
        user_id: Optional[ID] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Participants and settings of one conversation (disappearing messages, screen
        capture blocking, muted). No passcode needed."""
        return self._post(
            A.dm_conversation_info(self._session(session), conversation_id, user_id),
            response_format,
        )

    def set_disappearing(
        self,
        ttl_seconds: int,
        conversation_id: Optional[str] = None,
        *,
        user_id: Optional[ID] = None,
        passcode: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Turn disappearing messages on (``ttl_seconds`` from 60 to 31536000) or off (0).
        Returns the conversation after the change. Needs the passcode."""
        s = self._session(session)
        return self._post(
            A.dm_set_disappearing(s, ttl_seconds, conversation_id, user_id, passcode),
            response_format,
        )

    def send(
        self,
        text: str,
        conversation_id: Optional[str] = None,
        *,
        user_id: Optional[ID] = None,
        passcode: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Send an encrypted text message (up to 10,000 characters, no media) to a
        conversation or to a user. Needs the passcode; the recipient needs X Chat."""
        s = self._session(session)
        return self._post(
            A.dm_send(s, text, conversation_id, user_id, passcode), response_format
        )

    def settings(
        self,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Your DM settings: who can message you, read receipts, quality filter, calls."""
        return self._post(A.dm_settings(self._session(session)), response_format)

    def update_settings(
        self,
        *,
        allow_dms_from: Optional[str] = None,
        dm_receipt_settings: Optional[str] = None,
        always_allow_dms_from_subscribers: Optional[bool] = None,
        av_calls_enabled: Optional[bool] = None,
        accept_calls_from_everyone: Optional[bool] = None,
        accept_calls_from_following: Optional[bool] = None,
        accept_calls_from_verified: Optional[bool] = None,
        accept_calls_from_addressbook: Optional[bool] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Change your DM settings. Settings you leave out stay as they are; pass at least
        one. ``allow_dms_from`` and ``dm_receipt_settings`` take X's values (see
        :meth:`settings` for your current ones). Returns the settings after the change."""
        return self._post(
            A.dm_update_settings(
                self._session(session),
                allow_dms_from=allow_dms_from,
                dm_receipt_settings=dm_receipt_settings,
                always_allow_dms_from_subscribers=always_allow_dms_from_subscribers,
                av_calls_enabled=av_calls_enabled,
                accept_calls_from_everyone=accept_calls_from_everyone,
                accept_calls_from_following=accept_calls_from_following,
                accept_calls_from_verified=accept_calls_from_verified,
                accept_calls_from_addressbook=accept_calls_from_addressbook,
            ),
            response_format,
        )


class Account(SyncResource):
    """Actions with your own X account: post, reply, like, follow, upload media, edit your
    profile, read your bookmarks and more. ``client.account``.

    Every method runs as the :class:`~twittrapi.XSession` passed as ``session=``, or the
    client's ``session`` when none is passed. Answers are
    ``{"status_code": <X's status>, "response": "<X's JSON as a string>"}``; use
    :func:`twittrapi.unwrap_client_response` to parse ``response``, or
    ``response_format="simple"`` for the API's compact format.

    Actions that change something (everything except the reads such as :meth:`bookmarks`)
    are not retried after the request may have reached the API, so a retry never posts or
    likes twice. Rate limits (429) and connection failures are still retried.
    """

    lists: AccountLists
    communities: AccountCommunities
    drafts: AccountDrafts
    articles: AccountArticles
    dm: AccountDM

    def __init__(self, client: "TwittrAPI") -> None:
        super().__init__(client)
        self.lists = AccountLists(client)
        self.communities = AccountCommunities(client)
        self.drafts = AccountDrafts(client)
        self.articles = AccountArticles(client)
        self.dm = AccountDM(client)

    # Tweets

    def create_tweet(
        self,
        text: str,
        *,
        media_ids: Optional[Sequence[ID]] = None,
        possibly_sensitive: Optional[bool] = None,
        reply_settings: Optional[ReplySettings] = None,
        quote_url: Optional[str] = None,
        community_id: Optional[ID] = None,
        note_tweet: Optional[bool] = None,
        schedule_time: Optional[Union[int, datetime]] = None,
        poll_choices: Optional[Sequence[str]] = None,
        poll_duration_minutes: Optional[int] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Post a tweet.

        Over 280 characters (or with ``note_tweet=True``) it is sent as a long post.
        ``media_ids`` (up to 4) come from :meth:`upload_image` / :meth:`upload_video`.
        ``reply_settings`` limits who can reply: ``"only_follows"``, ``"only_verified"`` or
        ``"only_mentioned"`` (not used for community tweets). ``quote_url`` quotes a tweet,
        ``community_id`` posts into a community.

        ``schedule_time`` (Unix seconds or a ``datetime``) schedules the tweet instead; then
        only text and media are used.

        ``poll_choices`` (2 to 4, each up to 25 characters) adds a poll lasting
        ``poll_duration_minutes`` (5 to 10080, default 1 day). Polls cannot be combined with
        media, quotes, communities or scheduling, and are limited to 280 characters.
        """
        return self._post(
            A.create_tweet(
                self._session(session),
                text,
                media_ids=media_ids,
                possibly_sensitive=possibly_sensitive,
                reply_settings=reply_settings,
                quote_url=quote_url,
                community_id=community_id,
                note_tweet=note_tweet,
                schedule_time=schedule_time,
                poll_choices=poll_choices,
                poll_duration_minutes=poll_duration_minutes,
            ),
            response_format,
        )

    def reply(
        self,
        tweet_id: ID,
        text: str,
        *,
        media_ids: Optional[Sequence[ID]] = None,
        quote_url: Optional[str] = None,
        possibly_sensitive: Optional[bool] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Reply to a tweet. ``quote_url`` quotes another tweet in the reply."""
        return self._post(
            A.reply(
                self._session(session),
                tweet_id,
                text,
                media_ids=media_ids,
                quote_url=quote_url,
                possibly_sensitive=possibly_sensitive,
            ),
            response_format,
        )

    def delete_tweet(
        self,
        tweet_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Delete one of your tweets."""
        return self._tweet("delete_tweet", tweet_id, session, response_format)

    def like(
        self,
        tweet_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Like a tweet."""
        return self._tweet("like", tweet_id, session, response_format)

    def unlike(
        self,
        tweet_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Remove your like from a tweet."""
        return self._tweet("unlike", tweet_id, session, response_format)

    def retweet(
        self,
        tweet_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Retweet a tweet."""
        return self._tweet("retweet", tweet_id, session, response_format)

    def unretweet(
        self,
        tweet_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Undo a retweet. ``tweet_id`` is the original tweet."""
        return self._tweet("unretweet", tweet_id, session, response_format)

    def pin(
        self,
        tweet_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Pin one of your tweets to your profile."""
        return self._tweet("pin", tweet_id, session, response_format)

    def unpin(
        self,
        tweet_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Unpin a tweet from your profile."""
        return self._tweet("unpin", tweet_id, session, response_format)

    def bookmark(
        self,
        tweet_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Add a tweet to your bookmarks."""
        return self._tweet("bookmark", tweet_id, session, response_format)

    def unbookmark(
        self,
        tweet_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Remove a tweet from your bookmarks."""
        return self._tweet("unbookmark", tweet_id, session, response_format)

    def report(
        self,
        tweet_id: ID,
        user_id: ID,
        reason: ReportReason,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Report a tweet and its author (``user_id``, numeric) to X. ``reason`` is one of
        X's options such as ``"SpamSimpleOption"``."""
        return self._post(
            A.report(self._session(session), tweet_id, user_id, reason), response_format
        )

    def scheduled_tweets(
        self,
        *,
        ascending: Optional[bool] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Tweets scheduled on your account. Oldest first unless ``ascending=False``."""
        return self._post(A.scheduled_tweets(self._session(session), ascending), response_format)

    def delete_scheduled_tweet(
        self,
        scheduled_tweet_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Cancel a scheduled tweet (ID from :meth:`scheduled_tweets`)."""
        return self._post(
            A.delete_scheduled_tweet(self._session(session), scheduled_tweet_id), response_format
        )

    # Users

    def follow(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Follow an account, by ``user_id`` or ``username``."""
        return self._user("follow", user_id, username, session, response_format)

    def unfollow(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Unfollow an account, by ``user_id`` or ``username``."""
        return self._user("unfollow", user_id, username, session, response_format)

    def mute(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Mute an account, by ``user_id`` or ``username``."""
        return self._user("mute", user_id, username, session, response_format)

    def unmute(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Unmute an account, by ``user_id`` or ``username``."""
        return self._user("unmute", user_id, username, session, response_format)

    def block(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Block an account, by ``user_id`` or ``username``."""
        return self._user("block", user_id, username, session, response_format)

    def unblock(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Unblock an account, by ``user_id`` or ``username``."""
        return self._user("unblock", user_id, username, session, response_format)

    # Reads of your own account

    def home_timeline(
        self,
        *,
        count: Optional[int] = None,
        include_promoted_content: Optional[bool] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Your home timeline. ``count`` tweets to ask X for (default 20)."""
        return self._post(
            A.home_timeline(self._session(session), count, include_promoted_content),
            response_format,
        )

    def bookmarks(
        self,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Tweets in your bookmarks. Paginated."""
        return self._post(A.bookmarks(self._session(session), count, cursor), response_format)

    def bookmark_folders(
        self,
        *,
        cursor: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Your bookmark folders and their IDs. Paginated.

        Needs X Premium: without it X refuses with error code 37 ("Twitter Blue claim is not
        enabled").
        """
        return self._post(A.bookmark_folders(self._session(session), cursor), response_format)

    def bookmark_folder(
        self,
        folder_id: ID,
        *,
        cursor: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Tweets in one of your bookmark folders (``folder_id`` from
        :meth:`bookmark_folders`). Paginated. Needs X Premium."""
        return self._post(
            A.bookmark_folder(self._session(session), folder_id, cursor), response_format
        )

    def search_bookmarks(
        self,
        query: str,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Search your bookmarks (``query`` up to 500 characters). Paginated."""
        return self._post(
            A.search_bookmarks(self._session(session), query, count, cursor), response_format
        )

    def likes(
        self,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        user_id: Optional[ID] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Tweets you liked. Paginated. X shows likes only to the account itself, so this
        reads the session's account (from ``twid`` in the cookie; pass your own numeric
        ``user_id`` only if the cookie has no ``twid``)."""
        return self._post(
            A.likes(self._session(session), count, cursor, user_id), response_format
        )

    def blocked(
        self,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Accounts you blocked. Paginated."""
        return self._post(A.blocked(self._session(session), count, cursor), response_format)

    def muted(
        self,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Accounts you muted. Paginated."""
        return self._post(A.muted(self._session(session), count, cursor), response_format)

    def followers_you_know(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Followers of an account (``user_id`` or ``username``) that you follow.
        Paginated."""
        return self._post(
            A.followers_you_know(self._session(session), user_id, username, count, cursor),
            response_format,
        )

    # Media

    def upload_image(
        self,
        media: Media,
        *,
        media_type: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Upload an image and get a media ID for :meth:`create_tweet` or :meth:`reply`.

        ``media`` is the file as bytes (base64-encoded for you) or a base64 string. JPEG,
        PNG or WebP up to 5 MB, GIF up to 15 MB, at most 8192 x 8192 pixels. ``media_type``
        is optional: the API detects the type from the bytes. The ID is
        ``media_id_string`` inside ``response``.
        """
        return self._post(
            A.upload_image(self._session(session), media, media_type), response_format
        )

    def upload_video(
        self,
        media: Media,
        video_duration_ms: int,
        *,
        media_type: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Upload an MP4 or MOV video and get a media ID once X has processed it.

        ``video_duration_ms`` is the video's length. X allows 140 seconds without Premium.
        Request bodies are limited to 100 MB (a video of about 75 MB after base64). The
        call waits for X's processing, so give the client a long enough ``timeout``.
        """
        return self._post(
            A.upload_video(self._session(session), media, video_duration_ms, media_type),
            response_format,
        )

    def media_status(
        self,
        media_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Processing status of an uploaded media file."""
        return self._post(A.media_status(self._session(session), media_id), response_format)

    # Profile

    def update_profile(
        self,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        url: Optional[str] = None,
        birthdate: Optional[Birthdate] = None,
        remove_birthdate: bool = False,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Change your name (up to 50 characters, not empty), bio (``description``, 160),
        ``location`` (30), website (``url``, 100) or birth date. Fields you leave out stay
        as they are; an empty string clears description, location or url.

        ``birthdate`` is ``{"day", "month", "year"}`` plus optional ``visibility`` and
        ``year_visibility``; ``remove_birthdate=True`` removes it.
        """
        return self._post(
            A.update_profile(
                self._session(session),
                name=name,
                description=description,
                location=location,
                url=url,
                birthdate=birthdate,
                remove_birthdate=remove_birthdate,
            ),
            response_format,
        )

    def update_profile_image(
        self,
        media: Media,
        *,
        media_type: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Set your profile picture. JPEG, PNG or GIF up to 2 MB (400 x 400 recommended);
        crop it to a square first."""
        return self._post(
            A.update_profile_media("image", self._session(session), media, media_type),
            response_format,
        )

    def update_profile_banner(
        self,
        media: Media,
        *,
        media_type: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Set your header image. JPEG, PNG or GIF up to 5 MB, 3:1 (1500 x 500
        recommended); crop it first."""
        return self._post(
            A.update_profile_media("banner", self._session(session), media, media_type),
            response_format,
        )

    # Helpers

    def _tweet(
        self,
        kind: str,
        tweet_id: ID,
        session: Optional[XSession],
        response_format: Optional[ResponseFormat],
    ) -> Any:
        return self._post(A.tweet_action(kind, self._session(session), tweet_id), response_format)

    def _user(
        self,
        kind: str,
        user_id: Optional[ID],
        username: Optional[str],
        session: Optional[XSession],
        response_format: Optional[ResponseFormat],
    ) -> Any:
        return self._post(
            A.user_action(kind, self._session(session), user_id, username), response_format
        )


# ---------------------------------------------------------------------------
# Async


class AsyncAccountLists(AsyncResource):
    """Async version of :class:`AccountLists`."""

    async def create(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        private: Optional[bool] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Create a list. ``name`` up to 25 characters, ``description`` up to 100;
        ``private=True`` makes it visible only to you."""
        return await self._post(
            A.list_create(self._session(session), name, description, private), response_format
        )

    async def update(
        self,
        list_id: ID,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        private: Optional[bool] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Change a list's name, description or visibility. Pass at least one; the others
        stay as they are."""
        return await self._post(
            A.list_update(self._session(session), list_id, name, description, private),
            response_format,
        )

    async def delete(
        self,
        list_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Delete one of your lists."""
        return await self._post(A.list_delete(self._session(session), list_id), response_format)

    async def add_member(
        self,
        list_id: ID,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Add an account (``user_id`` or ``username``) to one of your lists."""
        return await self._post(
            A.list_member("add", self._session(session), list_id, user_id, username),
            response_format,
        )

    async def remove_member(
        self,
        list_id: ID,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Remove an account (``user_id`` or ``username``) from one of your lists."""
        return await self._post(
            A.list_member("remove", self._session(session), list_id, user_id, username),
            response_format,
        )


class AsyncAccountCommunities(AsyncResource):
    """Async version of :class:`AccountCommunities`."""

    async def create(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        join_policy: Optional[str] = None,
        invites_policy: Optional[str] = None,
        question: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Create a community owned by your account.

        ``join_policy`` (default ``"Open"``) and ``invites_policy`` (default
        ``"MemberInvitesAllowed"``) are passed to X as is. ``question`` is asked of people
        who request to join.
        """
        return await self._post(
            A.community_create(
                self._session(session), name, description, join_policy, invites_policy, question
            ),
            response_format,
        )

    async def delete(
        self,
        community_id: ID,
        name: str,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Delete a community you own. X wants its ``name`` together with the ID."""
        return await self._post(
            A.community_delete(self._session(session), community_id, name), response_format
        )

    async def join(
        self,
        community_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Join a community."""
        return await self._post(
            A.community_membership("join", self._session(session), community_id),
            response_format,
        )

    async def leave(
        self,
        community_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Leave a community."""
        return await self._post(
            A.community_membership("leave", self._session(session), community_id),
            response_format,
        )

    async def memberships(
        self,
        *,
        cursor: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Communities your account belongs to. Paginated."""
        return await self._post(
            A.community_memberships(self._session(session), cursor), response_format
        )


class AsyncAccountDrafts(AsyncResource):
    """Async version of :class:`AccountDrafts`."""

    async def list(
        self,
        *,
        ascending: Optional[bool] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Your drafts. Newest first unless ``ascending=True``."""
        return await self._post(A.drafts(self._session(session), ascending), response_format)

    async def create(
        self,
        text: Optional[str] = None,
        *,
        media_ids: Optional[Sequence[ID]] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Save a draft. Needs ``text`` or ``media_ids`` (up to 4)."""
        return await self._post(
            A.draft_create(self._session(session), text, media_ids), response_format
        )

    async def edit(
        self,
        draft_id: ID,
        text: Optional[str] = None,
        *,
        media_ids: Optional[Sequence[ID]] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Replace a draft's text and media. Needs ``text`` or ``media_ids``."""
        return await self._post(
            A.draft_edit(self._session(session), draft_id, text, media_ids), response_format
        )

    async def delete(
        self,
        draft_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Delete a draft."""
        return await self._post(A.draft_delete(self._session(session), draft_id), response_format)


class AsyncAccountArticles(AsyncResource):
    """Async version of :class:`AccountArticles`."""

    async def list(
        self,
        *,
        lifecycle: Optional[ArticleLifecycle] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        user_id: Optional[ID] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Your articles: ``lifecycle="draft"`` (default) or ``"published"``. Paginated.
        Needs X Premium.

        Reads the session's account (from ``twid`` in the cookie); pass your own numeric
        ``user_id`` only if the cookie has no ``twid``.
        """
        return await self._post(
            A.articles(self._session(session), lifecycle, count, cursor, user_id),
            response_format,
        )

    async def get(
        self,
        article_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """One of your articles: title, ``content_state``, cover, state and metadata.
        Needs X Premium."""
        return await self._post(A.article_get(self._session(session), article_id), response_format)

    async def create(
        self,
        *,
        title: Optional[str] = None,
        text: Optional[str] = None,
        content_state: Optional[Mapping[str, Any]] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Create a draft article. Needs X Premium.

        Everything is optional (without it the draft starts empty). Pass ``text`` or
        ``content_state``, not both. The answer holds the new draft and its ID.
        """
        return await self._post(
            A.article_create(self._session(session), title, text, content_state),
            response_format,
        )

    async def update(
        self,
        article_id: ID,
        *,
        title: Optional[str] = None,
        text: Optional[str] = None,
        content_state: Optional[Mapping[str, Any]] = None,
        cover_media_id: Optional[ID] = None,
        cover_media_category: Optional[ArticleCoverCategory] = None,
        remove_cover: bool = False,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Change an article's title, content or cover. Needs X Premium.

        ``text`` or ``content_state`` (not both) replaces the whole content.
        ``cover_media_id`` comes from :meth:`AsyncAccount.upload_image` or
        :meth:`AsyncAccount.upload_video`; ``cover_media_category`` is ``"DraftTweetImage"``
        (default), ``"DraftTweetGif"`` or ``"AmplifyVideo"``. ``remove_cover=True`` removes
        the cover (not together with ``cover_media_id``). Pass at least one change.
        """
        return await self._post(
            A.article_update(
                self._session(session),
                article_id,
                title=title,
                text=text,
                content_state=content_state,
                cover_media_id=cover_media_id,
                cover_media_category=cover_media_category,
                remove_cover=remove_cover,
            ),
            response_format,
        )

    async def publish(
        self,
        article_id: ID,
        *,
        visibility: Optional[ArticleVisibility] = None,
        reply_control: Optional[ArticleReplyControl] = None,
        tweet_text: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Publish a draft article as a post. Needs X Premium.

        ``visibility`` is ``"public"`` (default) or ``"subscribers"``. ``reply_control``
        (``"all"``, default, ``"community"``, ``"verified"`` or ``"byinvitation"``) is
        ignored for subscriber-only articles. ``tweet_text`` (up to 256 characters) is the
        text of the post that shares the article.
        """
        return await self._post(
            A.article_publish(
                self._session(session), article_id, visibility, reply_control, tweet_text
            ),
            response_format,
        )

    async def unpublish(
        self,
        article_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Turn a published article back into a draft. Needs X Premium."""
        return await self._post(
            A.article_action("unpublish", self._session(session), article_id), response_format
        )

    async def delete(
        self,
        article_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Delete an article. Needs X Premium."""
        return await self._post(
            A.article_action("delete", self._session(session), article_id), response_format
        )


class AsyncAccountDM(AsyncResource):
    """Async version of :class:`AccountDM`."""

    async def inbox(
        self,
        *,
        count: Optional[int] = None,
        passcode: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Your conversations (``count`` 1 to 50, default 20), with participants and
        settings. With a passcode each one also carries its latest messages, decrypted."""
        s = self._session(session)
        return await self._post(A.dm_inbox(s, count, passcode), response_format)

    async def conversation(
        self,
        conversation_id: Optional[str] = None,
        *,
        user_id: Optional[ID] = None,
        cursor: Optional[str] = None,
        passcode: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Messages of one conversation, decrypted, newest first. Paginated: pass the
        ``cursor`` of the previous page for older messages. Needs the passcode."""
        s = self._session(session)
        return await self._post(
            A.dm_conversation(s, conversation_id, user_id, cursor, passcode), response_format
        )

    async def conversation_info(
        self,
        conversation_id: Optional[str] = None,
        *,
        user_id: Optional[ID] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Participants and settings of one conversation (disappearing messages, screen
        capture blocking, muted). No passcode needed."""
        return await self._post(
            A.dm_conversation_info(self._session(session), conversation_id, user_id),
            response_format,
        )

    async def set_disappearing(
        self,
        ttl_seconds: int,
        conversation_id: Optional[str] = None,
        *,
        user_id: Optional[ID] = None,
        passcode: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Turn disappearing messages on (``ttl_seconds`` from 60 to 31536000) or off (0).
        Returns the conversation after the change. Needs the passcode."""
        s = self._session(session)
        return await self._post(
            A.dm_set_disappearing(s, ttl_seconds, conversation_id, user_id, passcode),
            response_format,
        )

    async def send(
        self,
        text: str,
        conversation_id: Optional[str] = None,
        *,
        user_id: Optional[ID] = None,
        passcode: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Send an encrypted text message (up to 10,000 characters, no media) to a
        conversation or to a user. Needs the passcode; the recipient needs X Chat."""
        s = self._session(session)
        return await self._post(
            A.dm_send(s, text, conversation_id, user_id, passcode), response_format
        )

    async def settings(
        self,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Your DM settings: who can message you, read receipts, quality filter, calls."""
        return await self._post(A.dm_settings(self._session(session)), response_format)

    async def update_settings(
        self,
        *,
        allow_dms_from: Optional[str] = None,
        dm_receipt_settings: Optional[str] = None,
        always_allow_dms_from_subscribers: Optional[bool] = None,
        av_calls_enabled: Optional[bool] = None,
        accept_calls_from_everyone: Optional[bool] = None,
        accept_calls_from_following: Optional[bool] = None,
        accept_calls_from_verified: Optional[bool] = None,
        accept_calls_from_addressbook: Optional[bool] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Change your DM settings. Settings you leave out stay as they are; pass at least
        one. ``allow_dms_from`` and ``dm_receipt_settings`` take X's values (see
        :meth:`settings` for your current ones). Returns the settings after the change."""
        return await self._post(
            A.dm_update_settings(
                self._session(session),
                allow_dms_from=allow_dms_from,
                dm_receipt_settings=dm_receipt_settings,
                always_allow_dms_from_subscribers=always_allow_dms_from_subscribers,
                av_calls_enabled=av_calls_enabled,
                accept_calls_from_everyone=accept_calls_from_everyone,
                accept_calls_from_following=accept_calls_from_following,
                accept_calls_from_verified=accept_calls_from_verified,
                accept_calls_from_addressbook=accept_calls_from_addressbook,
            ),
            response_format,
        )


class AsyncAccount(AsyncResource):
    """Async version of :class:`Account`."""

    lists: AsyncAccountLists
    communities: AsyncAccountCommunities
    drafts: AsyncAccountDrafts
    articles: AsyncAccountArticles
    dm: AsyncAccountDM

    def __init__(self, client: "AsyncTwittrAPI") -> None:
        super().__init__(client)
        self.lists = AsyncAccountLists(client)
        self.communities = AsyncAccountCommunities(client)
        self.drafts = AsyncAccountDrafts(client)
        self.articles = AsyncAccountArticles(client)
        self.dm = AsyncAccountDM(client)

    # Tweets

    async def create_tweet(
        self,
        text: str,
        *,
        media_ids: Optional[Sequence[ID]] = None,
        possibly_sensitive: Optional[bool] = None,
        reply_settings: Optional[ReplySettings] = None,
        quote_url: Optional[str] = None,
        community_id: Optional[ID] = None,
        note_tweet: Optional[bool] = None,
        schedule_time: Optional[Union[int, datetime]] = None,
        poll_choices: Optional[Sequence[str]] = None,
        poll_duration_minutes: Optional[int] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Post a tweet.

        Over 280 characters (or with ``note_tweet=True``) it is sent as a long post.
        ``media_ids`` (up to 4) come from :meth:`upload_image` / :meth:`upload_video`.
        ``reply_settings`` limits who can reply: ``"only_follows"``, ``"only_verified"`` or
        ``"only_mentioned"`` (not used for community tweets). ``quote_url`` quotes a tweet,
        ``community_id`` posts into a community.

        ``schedule_time`` (Unix seconds or a ``datetime``) schedules the tweet instead; then
        only text and media are used.

        ``poll_choices`` (2 to 4, each up to 25 characters) adds a poll lasting
        ``poll_duration_minutes`` (5 to 10080, default 1 day). Polls cannot be combined with
        media, quotes, communities or scheduling, and are limited to 280 characters.
        """
        return await self._post(
            A.create_tweet(
                self._session(session),
                text,
                media_ids=media_ids,
                possibly_sensitive=possibly_sensitive,
                reply_settings=reply_settings,
                quote_url=quote_url,
                community_id=community_id,
                note_tweet=note_tweet,
                schedule_time=schedule_time,
                poll_choices=poll_choices,
                poll_duration_minutes=poll_duration_minutes,
            ),
            response_format,
        )

    async def reply(
        self,
        tweet_id: ID,
        text: str,
        *,
        media_ids: Optional[Sequence[ID]] = None,
        quote_url: Optional[str] = None,
        possibly_sensitive: Optional[bool] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Reply to a tweet. ``quote_url`` quotes another tweet in the reply."""
        return await self._post(
            A.reply(
                self._session(session),
                tweet_id,
                text,
                media_ids=media_ids,
                quote_url=quote_url,
                possibly_sensitive=possibly_sensitive,
            ),
            response_format,
        )

    async def delete_tweet(
        self,
        tweet_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Delete one of your tweets."""
        return await self._tweet("delete_tweet", tweet_id, session, response_format)

    async def like(
        self,
        tweet_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Like a tweet."""
        return await self._tweet("like", tweet_id, session, response_format)

    async def unlike(
        self,
        tweet_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Remove your like from a tweet."""
        return await self._tweet("unlike", tweet_id, session, response_format)

    async def retweet(
        self,
        tweet_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Retweet a tweet."""
        return await self._tweet("retweet", tweet_id, session, response_format)

    async def unretweet(
        self,
        tweet_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Undo a retweet. ``tweet_id`` is the original tweet."""
        return await self._tweet("unretweet", tweet_id, session, response_format)

    async def pin(
        self,
        tweet_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Pin one of your tweets to your profile."""
        return await self._tweet("pin", tweet_id, session, response_format)

    async def unpin(
        self,
        tweet_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Unpin a tweet from your profile."""
        return await self._tweet("unpin", tweet_id, session, response_format)

    async def bookmark(
        self,
        tweet_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Add a tweet to your bookmarks."""
        return await self._tweet("bookmark", tweet_id, session, response_format)

    async def unbookmark(
        self,
        tweet_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Remove a tweet from your bookmarks."""
        return await self._tweet("unbookmark", tweet_id, session, response_format)

    async def report(
        self,
        tweet_id: ID,
        user_id: ID,
        reason: ReportReason,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Report a tweet and its author (``user_id``, numeric) to X. ``reason`` is one of
        X's options such as ``"SpamSimpleOption"``."""
        return await self._post(
            A.report(self._session(session), tweet_id, user_id, reason), response_format
        )

    async def scheduled_tweets(
        self,
        *,
        ascending: Optional[bool] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Tweets scheduled on your account. Oldest first unless ``ascending=False``."""
        return await self._post(A.scheduled_tweets(self._session(session), ascending), response_format)

    async def delete_scheduled_tweet(
        self,
        scheduled_tweet_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Cancel a scheduled tweet (ID from :meth:`scheduled_tweets`)."""
        return await self._post(
            A.delete_scheduled_tweet(self._session(session), scheduled_tweet_id), response_format
        )

    # Users

    async def follow(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Follow an account, by ``user_id`` or ``username``."""
        return await self._user("follow", user_id, username, session, response_format)

    async def unfollow(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Unfollow an account, by ``user_id`` or ``username``."""
        return await self._user("unfollow", user_id, username, session, response_format)

    async def mute(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Mute an account, by ``user_id`` or ``username``."""
        return await self._user("mute", user_id, username, session, response_format)

    async def unmute(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Unmute an account, by ``user_id`` or ``username``."""
        return await self._user("unmute", user_id, username, session, response_format)

    async def block(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Block an account, by ``user_id`` or ``username``."""
        return await self._user("block", user_id, username, session, response_format)

    async def unblock(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Unblock an account, by ``user_id`` or ``username``."""
        return await self._user("unblock", user_id, username, session, response_format)

    # Reads of your own account

    async def home_timeline(
        self,
        *,
        count: Optional[int] = None,
        include_promoted_content: Optional[bool] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Your home timeline. ``count`` tweets to ask X for (default 20)."""
        return await self._post(
            A.home_timeline(self._session(session), count, include_promoted_content),
            response_format,
        )

    async def bookmarks(
        self,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Tweets in your bookmarks. Paginated."""
        return await self._post(A.bookmarks(self._session(session), count, cursor), response_format)

    async def bookmark_folders(
        self,
        *,
        cursor: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Your bookmark folders and their IDs. Paginated.

        Needs X Premium: without it X refuses with error code 37 ("Twitter Blue claim is not
        enabled").
        """
        return await self._post(A.bookmark_folders(self._session(session), cursor), response_format)

    async def bookmark_folder(
        self,
        folder_id: ID,
        *,
        cursor: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Tweets in one of your bookmark folders (``folder_id`` from
        :meth:`bookmark_folders`). Paginated. Needs X Premium."""
        return await self._post(
            A.bookmark_folder(self._session(session), folder_id, cursor), response_format
        )

    async def search_bookmarks(
        self,
        query: str,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Search your bookmarks (``query`` up to 500 characters). Paginated."""
        return await self._post(
            A.search_bookmarks(self._session(session), query, count, cursor), response_format
        )

    async def likes(
        self,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        user_id: Optional[ID] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Tweets you liked. Paginated. X shows likes only to the account itself, so this
        reads the session's account (from ``twid`` in the cookie; pass your own numeric
        ``user_id`` only if the cookie has no ``twid``)."""
        return await self._post(
            A.likes(self._session(session), count, cursor, user_id), response_format
        )

    async def blocked(
        self,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Accounts you blocked. Paginated."""
        return await self._post(A.blocked(self._session(session), count, cursor), response_format)

    async def muted(
        self,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Accounts you muted. Paginated."""
        return await self._post(A.muted(self._session(session), count, cursor), response_format)

    async def followers_you_know(
        self,
        user_id: Optional[ID] = None,
        *,
        username: Optional[str] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Followers of an account (``user_id`` or ``username``) that you follow.
        Paginated."""
        return await self._post(
            A.followers_you_know(self._session(session), user_id, username, count, cursor),
            response_format,
        )

    # Media

    async def upload_image(
        self,
        media: Media,
        *,
        media_type: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Upload an image and get a media ID for :meth:`create_tweet` or :meth:`reply`.

        ``media`` is the file as bytes (base64-encoded for you) or a base64 string. JPEG,
        PNG or WebP up to 5 MB, GIF up to 15 MB, at most 8192 x 8192 pixels. ``media_type``
        is optional: the API detects the type from the bytes. The ID is
        ``media_id_string`` inside ``response``.
        """
        return await self._post(
            A.upload_image(self._session(session), media, media_type), response_format
        )

    async def upload_video(
        self,
        media: Media,
        video_duration_ms: int,
        *,
        media_type: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Upload an MP4 or MOV video and get a media ID once X has processed it.

        ``video_duration_ms`` is the video's length. X allows 140 seconds without Premium.
        Request bodies are limited to 100 MB (a video of about 75 MB after base64). The
        call waits for X's processing, so give the client a long enough ``timeout``.
        """
        return await self._post(
            A.upload_video(self._session(session), media, video_duration_ms, media_type),
            response_format,
        )

    async def media_status(
        self,
        media_id: ID,
        *,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Processing status of an uploaded media file."""
        return await self._post(A.media_status(self._session(session), media_id), response_format)

    # Profile

    async def update_profile(
        self,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        url: Optional[str] = None,
        birthdate: Optional[Birthdate] = None,
        remove_birthdate: bool = False,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Change your name (up to 50 characters, not empty), bio (``description``, 160),
        ``location`` (30), website (``url``, 100) or birth date. Fields you leave out stay
        as they are; an empty string clears description, location or url.

        ``birthdate`` is ``{"day", "month", "year"}`` plus optional ``visibility`` and
        ``year_visibility``; ``remove_birthdate=True`` removes it.
        """
        return await self._post(
            A.update_profile(
                self._session(session),
                name=name,
                description=description,
                location=location,
                url=url,
                birthdate=birthdate,
                remove_birthdate=remove_birthdate,
            ),
            response_format,
        )

    async def update_profile_image(
        self,
        media: Media,
        *,
        media_type: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Set your profile picture. JPEG, PNG or GIF up to 2 MB (400 x 400 recommended);
        crop it to a square first."""
        return await self._post(
            A.update_profile_media("image", self._session(session), media, media_type),
            response_format,
        )

    async def update_profile_banner(
        self,
        media: Media,
        *,
        media_type: Optional[str] = None,
        session: Optional[XSession] = None,
        response_format: Optional[ResponseFormat] = None,
    ) -> Any:
        """Set your header image. JPEG, PNG or GIF up to 5 MB, 3:1 (1500 x 500
        recommended); crop it first."""
        return await self._post(
            A.update_profile_media("banner", self._session(session), media, media_type),
            response_format,
        )

    # Helpers

    async def _tweet(
        self,
        kind: str,
        tweet_id: ID,
        session: Optional[XSession],
        response_format: Optional[ResponseFormat],
    ) -> Any:
        return await self._post(A.tweet_action(kind, self._session(session), tweet_id), response_format)

    async def _user(
        self,
        kind: str,
        user_id: Optional[ID],
        username: Optional[str],
        session: Optional[XSession],
        response_format: Optional[ResponseFormat],
    ) -> Any:
        return await self._post(
            A.user_action(kind, self._session(session), user_id, username), response_format
        )
