# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-10-16

### Added

- Account actions with your own X session: `client.account` (and `AsyncTwittrAPI.account`).
  Post (text, media, quotes, long posts, community tweets, polls, scheduled tweets), reply,
  delete, like / unlike, retweet / unretweet, pin / unpin, bookmark / unbookmark, report,
  follow / unfollow, mute / unmute, block / unblock, scheduled tweets, home timeline, your
  bookmarks, likes, blocked and muted accounts, followers you know, image and video upload,
  media status, profile, profile picture and header. Groups: `account.lists` (create, update,
  delete, add / remove members), `account.communities` (create, delete, join, leave),
  `account.drafts` (list, create, edit, delete) and `account.dm` (inbox, conversation,
  conversation info, disappearing messages, send, settings, update settings).
- `XSession(cookie=..., proxy=..., passcode=None)`: the X session the actions run as. Pass it to
  the client as `session=` or per call. `repr()` and `str()` hide all three values.
- `unwrap_client_response()` parses the `response` string of an account action's answer.
  `paginate()` reads it too, so account reads (bookmarks, likes, ...) and DM conversations
  paginate like the other endpoints.

### Changed

- Account actions that change something are retried only on 429 and on connection errors
  (the request never reached the API), not on timeouts or 5xx, so a retry cannot repeat an
  action. Reads keep the usual retries.

## [1.0.0] - 2026-10-15

First stable release: the API is stable and follows semantic versioning.

### Added

- `rapidapi_host` option on `TwittrAPI` and `AsyncTwittrAPI` (and the `RAPIDAPI_HOST`
  environment variable) for customers subscribed to another TwittrAPI listing on RapidAPI. It
  sets the `x-rapidapi-host` header and the base URL (`https://<host>`, unless `base_url` is
  passed). Accepts a bare host or a URL like `https://twttr.p.rapidapi.com/`; values with a path
  or spaces raise `ValueError`. The default stays `twitter-aio.p.rapidapi.com`, direct mode
  ignores it. The client exposes the host as `client.rapidapi_host`.

## [0.3.0] - 2026-10-14

### Changed

- **Breaking:** `tweets.likers` now sends POST with a JSON body and requires the keyword
  arguments `cookie` (the Cookie header of the account that posted the tweet, with `auth_token`
  and `ct0`) and `proxy` (`http://user:pass@host:port`). `count` and `cursor` go in the body;
  `paginate()` works as before. X shows likers only to the tweet's author, so this works only for
  your own tweets. The API now answers a GET, or a body without cookie or proxy, with 400.

## [0.2.1] - 2026-10-14

### Changed

- `users.get_many` accepts up to 500 IDs per call (was 100), matching the API.

## [0.2.0] - 2026-10-11

### Added

- Opt-in simple response format (`format=simple`, see https://twittrapi.com/docs/simple-format):
  `TwittrAPI(response_format="simple")` / `AsyncTwittrAPI(response_format="simple")` for the
  whole client, and a `response_format="raw" | "simple"` keyword on every resource method to
  override it per call. The default stays `"raw"`; raw requests are sent exactly as before.
- Typed models for the simple format in `twittrapi.models`: `Tweet`, `User`, `Page`
  (`data`, `next_cursor`, `previous_cursor`, `has_next_page`) and their parts (`TweetCounts`,
  `UserCounts`, `Media`, `ReplyTo`, `UserRef`, `Article`, `UnavailableTweet`), plus the
  `tweets_page()`, `users_page()` and `parse_tweet()` helpers.
- `paginate()` follows `nextCursor` until `hasNextPage` is false when the simple format is
  active (client default or `response_format="simple"` passed to `paginate()`). Raw pagination
  is unchanged, and a raw body on a simple request falls back to it.
- `simple_next_cursor()` and the `ResponseFormat` type are exported from `twittrapi`.
- Tests against the API's simple-format output (`tests/fixtures/simple/`).
- Tests against trimmed real API responses (`tests/fixtures/live/`): followers (Bottom cursor
  before Top), tweet detail, search wrapper, slice `next_cursor`, empty likes and favorites
  timelines, articles with an empty `tweet_results`.

### Changed

- `count` must be between 1 and 100 (`MAX_COUNT`), matching the API and the other TwittrAPI
  SDKs. Larger values now raise `ValueError` before any request is sent.
- Usernames: only one leading `@` is stripped.

### Fixed

- `paginate()` also stops on slice-based pages (communities search, jobs search) that return a
  `next_cursor` but no items.

## [0.1.0] - 2026-10-10

### Added

- `TwittrAPI` (sync) and `AsyncTwittrAPI` (async) clients.
- Direct API auth (`api_key`, `X-API-KEY`) and RapidAPI auth (`rapidapi_key`), with
  `TWITTRAPI_API_KEY` / `RAPIDAPI_KEY` / `TWITTRAPI_BASE_URL` environment variables.
- Resources for all 23 read endpoints: `users`, `tweets`, `search`, `lists`, `communities`,
  `trends`.
- Typed exceptions: `ValidationError`, `AuthenticationError`, `InsufficientBalanceError`,
  `NotFoundError`, `RateLimitError` (with `retry_after`), `ServerError`, `APIConnectionError`,
  `APITimeoutError`.
- Automatic retries with exponential backoff for 429, 5xx and network errors.
- `paginate()` and `extract_bottom_cursor()` for following X's timeline cursors (best-effort).
- `py.typed` marker.

[1.0.0]: https://github.com/twittrapi/twittrapi-python/compare/v0.3.0...v1.0.0
[0.3.0]: https://github.com/twittrapi/twittrapi-python/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/twittrapi/twittrapi-python/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/twittrapi/twittrapi-python/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/twittrapi/twittrapi-python/releases/tag/v0.1.0
