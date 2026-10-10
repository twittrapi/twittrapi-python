"""Print trending topics for a country or city by name.

    export TWITTRAPI_API_KEY=...
    python examples/trends_by_country.py Germany
    python examples/trends_by_country.py --list     # show every location with trends

Looks up the WOEID with client.trends.locations(), then calls client.trends.get().
"""

import argparse
import json
import sys
from typing import Any, Dict, Iterator, List

from twittrapi import TwittrAPI


def iter_dicts(data: Any) -> Iterator[Dict[str, Any]]:
    if isinstance(data, dict):
        yield data
        for value in data.values():
            yield from iter_dicts(value)
    elif isinstance(data, list):
        for item in data:
            yield from iter_dicts(item)


def locations(data: Any) -> List[Dict[str, Any]]:
    return [d for d in iter_dicts(data) if "woeid" in d and "name" in d]


def trend_names(data: Any) -> List[str]:
    names = []
    for d in iter_dicts(data):
        trends = d.get("trends")
        if isinstance(trends, list):
            names += [t["name"] for t in trends if isinstance(t, dict) and isinstance(t.get("name"), str)]
    return names


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("place", nargs="?", default="Worldwide")
    parser.add_argument("--list", action="store_true", help="list all locations")
    args = parser.parse_args()

    with TwittrAPI() as client:
        places = locations(client.trends.locations())
        if args.list:
            for p in sorted(places, key=lambda p: (p.get("country", ""), p["name"])):
                print(f"{p['woeid']:>10}  {p['name']}  ({p.get('country') or 'worldwide'})")
            return

        wanted = args.place.casefold()
        match = next((p for p in places if str(p["name"]).casefold() == wanted), None)
        if match is None:
            sys.exit(f"No trend location named {args.place!r}. Try --list.")

        data = client.trends.get(match["woeid"])

    names = trend_names(data)
    if not names:  # unknown shape: show the raw JSON
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return
    print(f"Trends for {match['name']} (WOEID {match['woeid']}):")
    for i, name in enumerate(names, 1):
        print(f"{i:>3}. {name}")


if __name__ == "__main__":
    main()
