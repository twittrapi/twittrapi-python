# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

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

[Unreleased]: https://github.com/twittrapi/twittrapi-python/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/twittrapi/twittrapi-python/releases/tag/v0.1.0
