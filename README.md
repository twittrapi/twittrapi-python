<p align="center">
  <a href="https://twittrapi.com"><img src=".github/banner.png" alt="twittrapi-python: Python client for Twitter/X data, sync and async, no X developer account" width="100%"></a>
</p>

# twittrapi – Twitter/X API client for Python

[![PyPI](https://img.shields.io/pypi/v/twittrapi.svg)](https://pypi.org/project/twittrapi/) [![Python](https://img.shields.io/pypi/pyversions/twittrapi.svg)](https://pypi.org/project/twittrapi/) [![Tests](https://github.com/twittrapi/twittrapi-python/actions/workflows/test.yml/badge.svg)](https://github.com/twittrapi/twittrapi-python/actions)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Official Python client for [TwittrAPI](https://twittrapi.com), a REST API for public Twitter/X data:
tweets, profiles, followers, search, lists and communities, plus actions with your own X account
(post, like, follow, DMs). From $0.065 per 1,000 calls, no X developer account.

> **Get an API key:** [twittrapi.com/start](https://twittrapi.com/start?utm_source=github&utm_medium=readme&utm_campaign=twittrapi-python) · [Pricing](https://twittrapi.com/pricing?utm_source=github&utm_medium=readme&utm_campaign=twittrapi-python) · [Docs](https://twittrapi.com/docs?utm_source=github&utm_medium=readme&utm_campaign=twittrapi-python) · [Status](https://twittrapi.com/status) · also available on [RapidAPI](https://rapidapi.com/viperscores-viperscores-default/api/twitter-aio)

**SDKs and integrations:** [Node.js](https://github.com/twittrapi/twittrapi-node) · [Go](https://github.com/twittrapi/twittrapi-go) · [MCP server](https://github.com/twittrapi/twittrapi-mcp) · [n8n](https://github.com/twittrapi/n8n-nodes-twittrapi) · [Make](https://www.make.com/en/hq/app-invitation/bfe92727f14ab2c74d3c2e74281d84b1) · [Apify](https://github.com/twittrapi/twittrapi-apify) · [LangChain](https://github.com/twittrapi/langchain-twittrapi) · [LlamaIndex](https://github.com/twittrapi/llama-index-tools-twittrapi) · [Agent skill](https://github.com/twittrapi/twittrapi-skills) · [Examples](https://github.com/twittrapi/twittrapi-examples)

- Sync (`TwittrAPI`) and async (`AsyncTwittrAPI`) clients with the same methods
- Works with a direct TwittrAPI key or a RapidAPI key
- Retries 429, 5xx and network errors with backoff
- Typed exceptions for every error class
- A cursor-following paginator
- Account actions with your own X session: post, reply, like, follow, upload media, DMs
- Python 3.9+, one dependency (`httpx`), fully type-annotated

Responses are X's raw GraphQL JSON, returned as plain `dict`/`list` values. The client does not
reshape them.

Not affiliated with X Corp.

## Install

```bash
pip install twittrapi
```

## Quickstart

### Direct API key

Get a key at [twittrapi.com](https://twittrapi.com).

```python
from twittrapi import TwittrAPI

client = TwittrAPI(api_key="YOUR_KEY")
user = client.users.get_by_username("jack")
print(user)
```

Requests go to `https://api.twittrapi.com` with an `X-API-KEY` header.

### RapidAPI key

```python
from twittrapi import TwittrAPI

client = TwittrAPI(rapidapi_key="YOUR_RAPIDAPI_KEY")
user = client.users.get_by_username("jack")
```

Requests go to `https://twitter-aio.p.rapidapi.com` with `x-rapidapi-key` and `x-rapidapi-host`
headers.

Subscribed to another TwittrAPI listing on RapidAPI? Set its host:
`TwittrAPI(rapidapi_key="...", rapidapi_host="twttr.p.rapidapi.com")`, or the `RAPIDAPI_HOST`
environment variable.

### Environment variables

With no key argument, the client reads `TWITTRAPI_API_KEY`, then `RAPIDAPI_KEY`:

```bash
export TWITTRAPI_API_KEY=YOUR_KEY
```

```python
client = TwittrAPI()
```

`TWITTRAPI_BASE_URL` overrides the direct API base URL (useful for a proxy or staging).

### Client options

```python
client = TwittrAPI(
    api_key="YOUR_KEY",
    base_url="https://api.twittrapi.com",  # default depends on the auth mode
    timeout=60.0,                          # seconds, or an httpx.Timeout
    max_retries=2,                         # retries for 429, 5xx and network errors
    response_format="raw",                 # or "simple", see "Simple format" below
)
```

You can also pass your own `httpx.Client` (or `httpx.AsyncClient`) as `http_client=` to set
proxies, transports or connection limits. The client does not close an `http_client` you pass in.

Close the client when done, or use it as a context manager:

```python
with TwittrAPI() as client:
    ...
```

## Examples by resource

IDs can be passed as `str` or `int`. Usernames can include a leading `@`.

### Users

```python
client.users.get_by_username("jack")
client.users.get_by_id("12")
client.users.username_to_id("jack")             # smaller response when you only need the ID
client.users.get_many(["12", "44196397"])       # up to 500 IDs per call

# Timelines take user_id or username=
client.users.tweets("12", count=20)
client.users.tweets(username="jack")
client.users.tweets_and_replies("12")
client.users.media("12")
client.users.followers("12", count=100)
client.users.following(username="jack")
client.users.verified_followers("12")
client.users.affiliates(username="XDevelopers")   # accounts affiliated with an organization

# Batch lookups by handle (duplicates dropped, billed one call per handle)
client.users.friendships_batch("jack", ["elonmusk", "XDevelopers"])  # up to 50 targets
client.users.about_batch(["jack", "XDevelopers"])                   # "About this account", up to 20
```

Passing `user_id` is a little faster than `username`, because the API does not have to look the
handle up first.

### Tweets

```python
client.tweets.get("1585841080431321088")                         # tweet plus reply thread
client.tweets.get("1585841080431321088", ranking_mode="Recency")  # Relevance, Recency or Likes
client.tweets.replies("1585841080431321088", ranking_mode="Likes")  # only the replies, paginated
client.tweets.thread("1585841080431321088")                         # the author's thread, one call
client.tweets.retweeters("1585841080431321088")
client.tweets.quotes("1585841080431321088")
```

`likers` works only for your own tweets: X shows who liked a tweet only to its author. Pass the
cookie of the account that posted the tweet (with `auth_token` and `ct0`) and a proxy; the SDK
sends them as a POST body. For anyone else's tweet the list is empty.

```python
client.tweets.likers(
    "1585841080431321088",
    cookie="auth_token=...; ct0=...",
    proxy="http://user:pass@host:port",
)
```

### Search

```python
client.search.tweets("python")
client.search.tweets('from:jack "hello" lang:en', category="Latest", count=20)
```

`query` supports X search operators (`from:`, `to:`, `lang:`, `since:`, `until:`, `min_faves:`,
`filter:media`, `-filter:replies`, ...). `category` is one of `Top` (default), `Latest`,
`People`, `Photos`, `Videos`.

### Lists

```python
client.lists.details("1234567890")
client.lists.tweets("1234567890")
client.lists.members("1234567890")
```

### Communities

```python
client.communities.search("python")
client.communities.get("1500000000000000000")
client.communities.about("1500000000000000000")   # rules, moderators, members preview
client.communities.tweets("1500000000000000000")
```

### Spaces

```python
client.spaces.get("1YqKDqWqdPLsV")   # the ID from x.com/i/spaces/<id>
```

### Trends

```python
client.trends.get(1)          # worldwide
client.trends.get(23424977)   # United States
client.trends.locations()     # every location with trends, with its WOEID
```

## Account actions

`client.account` acts as your own X account: post, reply, like, retweet, follow, bookmark, upload
media, edit your profile, manage lists, communities, drafts and articles, and read or send direct
messages.

It needs your X session: the Cookie header of your logged-in account (`auth_token`, `ct0`, and
`twid` for DMs and likes) and your proxy (`http://user:pass@host:port`). How to get the cookie:
[twittrapi.com/docs/x-session](https://twittrapi.com/docs/x-session).

```python
from twittrapi import TwittrAPI, XSession, unwrap_client_response

session = XSession(
    cookie="auth_token=...; ct0=...; twid=u%3D...",
    proxy="http://user:pass@host:port",
)
client = TwittrAPI(api_key="YOUR_KEY", session=session)

client.account.create_tweet("Hello from the API")
client.account.reply("1585841080431321088", "Nice")
client.account.like("1585841080431321088")
client.account.follow(username="XDevelopers")

uploaded = unwrap_client_response(client.account.upload_image(open("photo.jpg", "rb").read()))
client.account.create_tweet("With a photo", media_ids=[uploaded["media_id_string"]])

client.account.create_tweet("Tabs or spaces?", poll_choices=["Tabs", "Spaces"])
client.account.update_profile(description="Building things", location="Berlin")

for page in client.paginate(client.account.bookmarks, max_pages=3):
    ...
```

You can also pass `session=` per call instead of to the client, e.g. to act as several accounts
with one client. `repr()` never shows the cookie, proxy or passcode.

The full list: `create_tweet`, `reply`, `delete_tweet`, `like` / `unlike`, `retweet` /
`unretweet`, `pin` / `unpin`, `bookmark` / `unbookmark`, `report`, `scheduled_tweets`,
`delete_scheduled_tweet`, `follow` / `unfollow`, `mute` / `unmute`, `block` / `unblock`,
`home_timeline`, `bookmarks`, `bookmark_folders`, `bookmark_folder`, `search_bookmarks`,
`likes`, `blocked`, `muted`, `followers_you_know`, `upload_image`, `upload_video`,
`media_status`, `update_profile`, `update_profile_image`, `update_profile_banner`, and the
groups `account.lists`, `account.communities` (including `memberships`), `account.drafts`,
`account.articles` and `account.dm`. Accounts can be given as `user_id` or `username=`.
Bookmark folders and articles need X Premium.

Answers are `{"status_code": ..., "response": "<X's JSON as a string>"}`;
`twittrapi.unwrap_client_response()` parses `response`. With `response_format="simple"` you get
the compact format instead.

Actions that change something are not retried after the request may have reached the API, so a
retry never posts twice. Reads like `bookmarks` retry as usual.

### Articles

Long-form X Articles. Needs X Premium.

```python
client.account.articles.create(title="Hello", text="First line\nSecond line")  # answer has the ID
client.account.articles.list()                        # drafts; lifecycle="published" for the others
client.account.articles.get("1846000000000000000")
client.account.articles.update("1846000000000000000", title="New title", cover_media_id="1234567890")
client.account.articles.publish("1846000000000000000", tweet_text="New article")
client.account.articles.unpublish("1846000000000000000")
client.account.articles.delete("1846000000000000000")
```

Content is plain `text` (one paragraph per line) or `content_state`, X's own format as `get`
returns it; not both.

### Direct messages

DMs on X are end-to-end encrypted. Reading and sending messages needs your X Chat passcode; it is
used for the request only and not stored.

```python
session = XSession(cookie="...", proxy="...", passcode="1234")
client = TwittrAPI(session=session)

client.account.dm.inbox()                         # conversations with their latest messages
client.account.dm.conversation(user_id="12")      # one chat, newest first, paginated
client.account.dm.send("Hello", user_id="12")
client.account.dm.settings()                      # no passcode needed
```

## Simple format

By default every method returns X's raw JSON. The API can also answer in a compact, flat,
camelCase format with a fixed schema ([docs](https://twittrapi.com/docs/simple-format)). It is
opt-in: set it for the whole client, or per call with `response_format=` on any method.

```python
client = TwittrAPI(response_format="simple")
page = client.users.tweets(username="XDevelopers", count=20)
# {"data": [{"id": ..., "text": ..., "author": {...}, "counts": {...}, ...}],
#  "nextCursor": "...", "previousCursor": "...", "hasNextPage": true}

raw = client.users.tweets(username="XDevelopers", response_format="raw")  # this call only
```

`twittrapi.models` has typed dataclasses for it (`Tweet`, `User`, `Page`, ...), with
snake_case attributes:

```python
from twittrapi.models import User, tweets_page, users_page

page = tweets_page(client.users.tweets(username="XDevelopers"))
for tweet in page.data:
    print(tweet.id, tweet.counts.likes, tweet.author.username if tweet.author else None)
print(page.next_cursor, page.has_next_page)

user = User.from_dict(client.users.get_by_username("XDevelopers")["data"])
```

Same price, parameters and errors as the raw format; only successful responses change.
Status routes ignore the option and answer as usual, and so do `spaces.get`,
`communities.about`, `users.friendships_batch`, `users.about_batch`, the bookmark folder and
bookmark search reads, `account.communities.memberships` and `account.articles`.

## Pagination

Paginated methods accept `count` (1 to 100; leave it out for the server default of 20) and
`cursor`. `count` is only a hint to X: a page can hold more or fewer results. X puts the next-page cursor inside the response
(a timeline entry with `cursorType: "Bottom"`). `client.paginate()` finds it and keeps calling
the method for you, yielding each raw page:

```python
for page in client.paginate(client.users.followers, username="jack", count=100, max_pages=5):
    ...  # page is the raw JSON for one request
```

Paging stops when any of these happens:

- `max_pages` pages were fetched (default 10, `None` for no limit)
- no bottom cursor is found in the page
- the cursor repeats
- the page has no results, only cursor entries

Each page is a separate billed request, so set `max_pages` to what you need.

To start from a saved cursor, pass `cursor=...`. If you want to page by hand, use
`extract_bottom_cursor`:

```python
from twittrapi import extract_bottom_cursor

page = client.search.tweets("python", category="Latest")
next_cursor = extract_bottom_cursor(page)
if next_cursor:
    page = client.search.tweets("python", category="Latest", cursor=next_cursor)
```

Cursor detection is best-effort. X does not document its response format, and the helper
searches the whole response for the shapes X uses today (`cursorType: "Bottom"` objects and
`cursor-bottom-*` entry IDs). If X changes the format, the paginator may stop early.

In the simple format none of this guessing is needed: every list response carries
`nextCursor` and `hasNextPage`, and `paginate()` follows `nextCursor` until `hasNextPage` is
false. That applies when the client was created with `response_format="simple"` or when you
pass `response_format="simple"` to `paginate()`:

```python
for page in client.paginate(client.users.followers, username="jack", response_format="simple"):
    for user in page["data"]:
        print(user["username"])
```

## Error handling

All errors raised by the client inherit from `TwittrAPIError`.

| Exception | When |
| --- | --- |
| `ValidationError` | 400, 422: bad parameters |
| `AuthenticationError` | 401, 403: missing or invalid key, or no access |
| `InsufficientBalanceError` | 402: no balance left on the account |
| `NotFoundError` | 404: user, tweet, list or community not found |
| `RateLimitError` | 429: too many requests; has `retry_after` (seconds or `None`) |
| `ServerError` | 5xx |
| `APIStatusError` | any other 4xx; base class of all the above |
| `APIConnectionError` | network failure, no response |
| `APITimeoutError` | request timed out (subclass of `APIConnectionError`) |

HTTP errors carry `status_code`, `message` (the API's `error` text), `body` (parsed JSON) and
`response` (the `httpx.Response`).

```python
from twittrapi import (
    TwittrAPI,
    InsufficientBalanceError,
    NotFoundError,
    RateLimitError,
    TwittrAPIError,
)

client = TwittrAPI()
try:
    user = client.users.get_by_username("someone")
except NotFoundError:
    print("No such user")
except InsufficientBalanceError:
    print("Top up at https://twittrapi.com")
except RateLimitError as exc:
    print(f"Rate limited, retry in {exc.retry_after}s")
except TwittrAPIError as exc:
    print(f"API error: {exc}")
```

Invalid arguments (a non-numeric ID, more than 500 IDs, an unknown `category`) raise
`ValueError` or `TypeError` before any request is sent.

### Retries

429 responses, 5xx responses and network errors are retried up to `max_retries` times (default 2,
so at most 3 attempts). The wait is 0.5 s, 1 s, 2 s, ... with some jitter, capped at 8 s. For 429
the client waits for the `Retry-After` header if the API sends one (capped at 60 s). Other 4xx
errors, including 402, are never retried. Set `max_retries=0` to turn retries off.

## Async

`AsyncTwittrAPI` has the same constructor and methods. Every API method is a coroutine, and
`paginate` returns an async iterator.

```python
import asyncio
from twittrapi import AsyncTwittrAPI


async def main() -> None:
    async with AsyncTwittrAPI() as client:
        user, trends = await asyncio.gather(
            client.users.get_by_username("jack"),
            client.trends.get(1),
        )
        async for page in client.paginate(client.search.tweets, "python", max_pages=3):
            ...


asyncio.run(main())
```

## More examples

The [`examples/`](examples) folder has short scripts:

- `export_followers_csv.py`: export a user's followers to CSV
- `keyword_monitor.py`: poll search and print new matching tweets
- `user_timeline_json.py`: save a user's tweets to JSON
- `trends_by_country.py`: trends for a country or city by name

## Development

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
.venv/bin/mypy
```

## Support

Questions, bugs or a higher rate limit: email support@twittrapi.com or open an issue in this repository. Service status: [twittrapi.com/status](https://twittrapi.com/status). News and changes: the TwittrAPI Telegram channel (link on the website).

## License

MIT. See [LICENSE](LICENSE).

TwittrAPI is an independent service and is not affiliated with, endorsed by or sponsored by
X Corp. "X" and "Twitter" are trademarks of X Corp.
