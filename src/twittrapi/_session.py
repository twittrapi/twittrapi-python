"""The X session used by account actions (``client.account``)."""

from __future__ import annotations

from typing import Optional

__all__ = ["XSession"]

_HIDDEN = "<hidden>"


def _required(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


class XSession:
    """A logged-in X session: the account the actions run as.

    ``cookie`` is the Cookie header of your own logged-in X session. It must contain
    ``auth_token`` and ``ct0``; direct messages and :meth:`~twittrapi.resources.Account.likes`
    also use ``twid`` (your account ID, set by x.com at login), as in
    ``"auth_token=...; ct0=...; twid=u%3D..."``. See https://twittrapi.com/docs/x-session.

    ``proxy`` is your proxy, ``http://user:pass@host:port``. The requests to X go out through
    it; it is used only for your requests.

    ``passcode`` (optional) is your X Chat passcode. Only the direct-message methods send it,
    and only when they need it; you can also pass it per call.

    The values are never shown by ``repr()`` or ``str()``, so a session can be logged safely.
    They are sent to TwittrAPI in the request body of each account action.
    """

    __slots__ = ("_cookie", "_proxy", "_passcode")
    _cookie: str
    _proxy: str
    _passcode: Optional[str]

    def __init__(self, cookie: str, proxy: str, *, passcode: Optional[str] = None) -> None:
        cookie = _required(cookie, "cookie")
        proxy = _required(proxy, "proxy")
        names = {
            part.split("=", 1)[0].strip() for part in cookie.split(";") if "=" in part
        }
        missing = [name for name in ("auth_token", "ct0") if name not in names]
        if missing:
            raise ValueError(
                "cookie must contain auth_token and ct0 (missing: " + ", ".join(missing) + ")"
            )
        if passcode is not None:
            passcode = _required(passcode, "passcode")
        object.__setattr__(self, "_cookie", cookie)
        object.__setattr__(self, "_proxy", proxy)
        object.__setattr__(self, "_passcode", passcode)

    @property
    def cookie(self) -> str:
        return self._cookie

    @property
    def proxy(self) -> str:
        return self._proxy

    @property
    def passcode(self) -> Optional[str]:
        return self._passcode

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("XSession is immutable")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, XSession):
            return NotImplemented
        return (self._cookie, self._proxy, self._passcode) == (
            other._cookie,
            other._proxy,
            other._passcode,
        )

    def __hash__(self) -> int:
        return hash((self._cookie, self._proxy, self._passcode))

    def __repr__(self) -> str:
        passcode = f", passcode={_HIDDEN}" if self._passcode is not None else ""
        return f"XSession(cookie={_HIDDEN}, proxy={_HIDDEN}{passcode})"

    __str__ = __repr__
