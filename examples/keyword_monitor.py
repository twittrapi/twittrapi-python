"""Poll X search and print new tweets that match a query.

    export TWITTRAPI_API_KEY=...
    python examples/keyword_monitor.py '"open source" lang:en -filter:replies' --interval 120

Every poll is one billed request. Stop with Ctrl+C.
"""

import argparse
import time
from typing import Any, Dict, Iterator

from twittrapi import RateLimitError, TwittrAPI, TwittrAPIError


def iter_tweets(data: Any) -> Iterator[Dict[str, Any]]:
    """Yields tweet objects (``tweet_results.result``) from a raw X response, best-effort."""
    if isinstance(data, dict):
        holder = data.get("tweet_results")
        if isinstance(holder, dict) and isinstance(holder.get("result"), dict):
            tweet = holder["result"]
            tweet = tweet.get("tweet", tweet)  # "TweetWithVisibilityResults" wraps the tweet
            if tweet.get("rest_id"):
                yield tweet
                return
        for value in data.values():
            yield from iter_tweets(value)
    elif isinstance(data, list):
        for item in data:
            yield from iter_tweets(item)


def author(tweet: Dict[str, Any]) -> str:
    user = tweet.get("core", {}).get("user_results", {}).get("result", {})
    return user.get("core", {}).get("screen_name") or user.get("legacy", {}).get("screen_name") or "?"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("query", help="X search query, operators allowed")
    parser.add_argument("--interval", type=int, default=120, help="seconds between polls")
    args = parser.parse_args()

    seen = set()
    first = True
    with TwittrAPI() as client:
        while True:
            try:
                page = client.search.tweets(args.query, category="Latest", count=20)
            except RateLimitError as exc:
                time.sleep(exc.retry_after or args.interval)
                continue
            except TwittrAPIError as exc:
                print(f"error: {exc}")
                time.sleep(args.interval)
                continue
            for tweet in reversed(list(iter_tweets(page))):
                if tweet["rest_id"] in seen:
                    continue
                seen.add(tweet["rest_id"])
                if not first:  # the first poll only fills `seen`
                    text = tweet.get("legacy", {}).get("full_text", "").replace("\n", " ")
                    print(f"@{author(tweet)}: {text}\n  https://x.com/i/status/{tweet['rest_id']}")
            first = False
            time.sleep(args.interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
