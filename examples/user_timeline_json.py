"""Save a user's recent tweets to a JSON file.

    export TWITTRAPI_API_KEY=...
    python examples/user_timeline_json.py jack tweets.json --max-pages 3

Writes a list of simplified tweets. Pass --raw to save the raw API pages instead.
"""

import argparse
import json
from typing import Any, Dict, Iterator

from twittrapi import TwittrAPI


def iter_tweets(data: Any) -> Iterator[Dict[str, Any]]:
    """Yields tweet objects (``tweet_results.result``) from a raw X response, best-effort."""
    if isinstance(data, dict):
        holder = data.get("tweet_results")
        if isinstance(holder, dict) and isinstance(holder.get("result"), dict):
            tweet = holder["result"]
            tweet = tweet.get("tweet", tweet)
            if tweet.get("rest_id"):
                yield tweet
                return
        for value in data.values():
            yield from iter_tweets(value)
    elif isinstance(data, list):
        for item in data:
            yield from iter_tweets(item)


def simplify(tweet: Dict[str, Any]) -> Dict[str, Any]:
    legacy = tweet.get("legacy", {})
    return {
        "id": tweet["rest_id"],
        "created_at": legacy.get("created_at"),
        "text": legacy.get("full_text"),
        "likes": legacy.get("favorite_count"),
        "retweets": legacy.get("retweet_count"),
        "replies": legacy.get("reply_count"),
        "views": tweet.get("views", {}).get("count"),
        "url": f"https://x.com/i/status/{tweet['rest_id']}",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("username")
    parser.add_argument("output")
    parser.add_argument("--max-pages", type=int, default=3)
    parser.add_argument("--raw", action="store_true", help="save raw API pages")
    args = parser.parse_args()

    with TwittrAPI() as client:
        pages = list(client.paginate(client.users.tweets, username=args.username, max_pages=args.max_pages))

    if args.raw:
        out: Any = pages
    else:
        tweets: Dict[str, Dict[str, Any]] = {}
        for page in pages:
            for tweet in iter_tweets(page):
                tweets.setdefault(tweet["rest_id"], simplify(tweet))
        out = list(tweets.values())

    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print(f"Wrote {len(out)} {'pages' if args.raw else 'tweets'} to {args.output}")


if __name__ == "__main__":
    main()
