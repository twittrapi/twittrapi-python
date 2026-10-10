"""Export a user's followers to a CSV file.

    export TWITTRAPI_API_KEY=...
    python examples/export_followers_csv.py jack followers.csv --max-pages 5

Each page is one billed request (about 20 followers per page by default, up to 100 with
--count). The JSON parsing below is best-effort: it reads X's raw response format.
"""

import argparse
import csv
from typing import Any, Dict, Iterator

from twittrapi import TwittrAPI


def iter_user_results(data: Any) -> Iterator[Dict[str, Any]]:
    """Yields every user object (``user_results.result``) found in a raw X response."""
    if isinstance(data, dict):
        holder = data.get("user_results")
        if isinstance(holder, dict) and isinstance(holder.get("result"), dict):
            if holder["result"].get("rest_id"):
                yield holder["result"]
                return
        for value in data.values():
            yield from iter_user_results(value)
    elif isinstance(data, list):
        for item in data:
            yield from iter_user_results(item)


def row(user: Dict[str, Any]) -> Dict[str, Any]:
    legacy = user.get("legacy", {})
    core = user.get("core", {})  # X moved some fields from legacy to core in 2025
    return {
        "id": user.get("rest_id"),
        "username": core.get("screen_name") or legacy.get("screen_name"),
        "name": core.get("name") or legacy.get("name"),
        "followers": legacy.get("followers_count"),
        "following": legacy.get("friends_count"),
        "verified": user.get("is_blue_verified"),
        "bio": legacy.get("description"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("username")
    parser.add_argument("output", help="CSV file to write")
    parser.add_argument("--max-pages", type=int, default=5)
    parser.add_argument("--count", type=int, default=100, help="followers per page, max 100")
    args = parser.parse_args()

    seen = set()
    with TwittrAPI() as client, open(args.output, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["id", "username", "name", "followers", "following", "verified", "bio"])
        writer.writeheader()
        pages = client.paginate(
            client.users.followers, username=args.username, count=args.count, max_pages=args.max_pages
        )
        for page in pages:
            for user in iter_user_results(page):
                if user["rest_id"] not in seen:
                    seen.add(user["rest_id"])
                    writer.writerow(row(user))
    print(f"Wrote {len(seen)} followers to {args.output}")


if __name__ == "__main__":
    main()
