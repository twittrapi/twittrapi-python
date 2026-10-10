"""Cursor extraction and page iteration for X's raw timeline JSON.

This is best-effort. TwittrAPI returns X's GraphQL responses unchanged, and X does not publish
a schema for them. In practice the "next page" cursor is a timeline entry shaped like::

    {"entryId": "cursor-bottom-...",
     "content": {"entryType": "TimelineTimelineCursor", "cursorType": "Bottom", "value": "..."}}

Sometimes it is nested under ``itemContent``, or delivered through a ``TimelineReplaceEntry``
instruction on later pages. :func:`extract_bottom_cursor` walks the whole response and looks for
any of those shapes, so it keeps working when X moves things around, but it can still miss a
cursor if X changes the format in a bigger way. When no cursor is found, iteration stops.
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional, Tuple

__all__ = ["extract_bottom_cursor", "count_content_entries"]

# Guard against pathological input; real responses are far smaller.
_MAX_NODES = 1_000_000


def _walk(data: Any) -> Iterator[Any]:
    """Yields every dict and list in ``data`` in document order, without recursion."""
    stack: List[Any] = [data]
    seen = 0
    while stack and seen < _MAX_NODES:
        node = stack.pop()
        seen += 1
        if isinstance(node, dict):
            yield node
            children = [v for v in node.values() if isinstance(v, (dict, list))]
        elif isinstance(node, list):
            yield node
            children = [v for v in node if isinstance(v, (dict, list))]
        else:
            continue
        stack.extend(reversed(children))


def _cursor_value(node: Any) -> Optional[str]:
    """Returns ``value`` from a cursor object or from its ``content``/``itemContent`` wrapper."""
    if not isinstance(node, dict):
        return None
    value = node.get("value")
    if isinstance(value, str) and value:
        return value
    for key in ("content", "itemContent"):
        inner = node.get(key)
        found = _cursor_value(inner)
        if found:
            return found
    return None


def _cursor_type(node: Dict[str, Any]) -> Optional[str]:
    value = node.get("cursorType", node.get("cursor_type"))
    return value if isinstance(value, str) else None


def extract_bottom_cursor(data: Any) -> Optional[str]:
    """Returns the cursor for the next page of ``data``, or ``None`` if none was found.

    Looks for, in document order:

    * objects with ``cursorType == "Bottom"`` and a string ``value``
    * timeline entries whose ``entryId`` starts with ``"cursor-bottom-"``
    * plain ``next_cursor`` / ``nextCursor`` string fields (other than ``"0"``)
    """
    for node in _walk(data):
        if not isinstance(node, dict):
            continue
        if _cursor_type(node) == "Bottom":
            value = node.get("value")
            if isinstance(value, str) and value:
                return value
        entry_id = node.get("entryId")
        if isinstance(entry_id, str) and entry_id.startswith("cursor-bottom-"):
            value = _cursor_value(node.get("content")) or _cursor_value(node.get("item"))
            if value:
                return value
        for key in ("next_cursor", "nextCursor"):
            value = node.get(key)
            if isinstance(value, str) and value and value != "0":
                return value
    return None


def count_content_entries(data: Any) -> Tuple[int, int]:
    """Counts timeline entries in ``data``.

    Returns ``(entry_lists_found, non_cursor_entries)``. An entry is any dict with an
    ``entryId`` inside an ``entries`` list; cursor entries (``entryId`` starting with ``"cursor-"``) are not counted as content.
    Used by the paginator to stop when X keeps returning a cursor but no more results.
    """
    lists = 0
    content = 0
    for node in _walk(data):
        if not isinstance(node, dict):
            continue
        entries = node.get("entries")
        if isinstance(entries, list):
            lists += 1
            for entry in entries:
                if isinstance(entry, dict):
                    entry_id = entry.get("entryId")
                    if isinstance(entry_id, str) and not entry_id.startswith("cursor-"):
                        content += 1
    return lists, content


def page_is_empty(data: Any) -> bool:
    """True when the response has timeline entry lists but none of them hold real results."""
    lists, content = count_content_entries(data)
    return lists > 0 and content == 0
