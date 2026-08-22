# Changelog

Notable changes to BetterTracker. Newest first.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) loosely.
This is a personal project with no releases, so entries are grouped by date
rather than version number.

Beyond *what* changed, entries record **why** — especially for decisions that
look arbitrary later (scoring weights, day-boundary rules, cache windows) and
for bugs whose cause was non-obvious. Migrations and manual steps are called
out explicitly, since forgetting one breaks the app on the next run.

---

## Deliberate decisions — do not revert

Each of these looks like a bug, an oversight, or a simplification worth
"cleaning up". Each is intentional, and several were arrived at only after the
naive version failed in practice. **Read the reason before changing any of
them**; if you still want to change one, update this list in the same commit.

| Decision | Why it looks wrong | Why it is right |
|---|---|---|
| CLI scripts (`backfill_health.py`, `calibrate_sleep_baseline.py`, `seed_games.py`) use `print()`, not logging | The server code was converted to logging; these look missed | `print()` is their user interface. Timestamps and level prefixes would wreck a readable progress table. |
| Sleep-onset latency is not scored | Google lists "time to sound sleep" as a component | This device reports `minutesToFallAsleep: 0` on **every** session. Scoring it would hand out free points on every night. |
| `Base.metadata.create_all()` is absent from app startup | Fresh clones need tables from somewhere | Alembic owns the schema (`make migrate`). `create_all` only ever created missing *tables* and silently ignored new *columns* — the reason column changes used to be hand-written `ALTER`s. |
| `connected` is based on the **refresh** token, not the access token | The access token is what requests actually use | The access token is a ~1h credential that `_fetch_data` renews on 401. Basing `connected` on it made the flag a one-way latch that could never report a dead grant. |
| The snapshot freshness rule lives in the **backend**, not the frontend | The frontend is what knows when it last rendered | Every open tab would make its own staleness decision — three tabs, three Google calls for the same data. Server-side, the TTL is correct for any number of clients. |
| Personal scoring anchors are **clamped** to healthy-adult bounds | It ignores part of the user's own data | Without clamps, a month of 3-hour nights drags the "full credit" target down to 3 hours, so the score flatters worsening habits. |
| A gaming day runs **4am–4am**, and sessions join to the **next** morning's snapshot | Calendar days and same-day joins are the obvious reading | A session at 1am belongs to the previous evening. A snapshot dated D holds the sleep that *ended* that morning, so gaming day D pairs with snapshot D+1. Same-day joins measure the wrong night. |
| Days past `HEALTH_SYNC_WINDOW_DAYS` are never refetched, even when `synced_at` is NULL | A NULL timestamp looks like "never synced, so fetch it" | Those days are settled — the watch uploaded them long ago and Google won't revise them. Rows written before the column existed have NULL forever; without this rule any historical date refetches on every request. |
| Insight metrics average over **days**, not sessions | Session count is the obvious denominator | Three sessions in one evening would otherwise count that night's sleep three times. |
| The health sync runs **at startup, then sleeps** | Sleeping first avoids hammering the API on a restart loop | Sleeping first meant a process restarting more often than the interval (`uvicorn --reload`) never reached its first fetch — 12 days of data went missing this way. A `last_success_at` guard covers the restart-storm case instead. |
| `_clear_reauth()` does **not** set `last_success_at` | Reconnecting feels like a success worth stamping | That field means "last actually pulled data". Stamping it on a token exchange made the sync's freshness guard skip the first real sync after every reconnect. |
| Dates are parsed as `` `${iso}T00:00:00` `` in the frontend | The suffix looks redundant | A bare `new Date("2026-08-22")` is parsed as **UTC**, rendering as the previous day in western timezones. |

---

## 2026-08-22

### Added
- **Test suite** (`pytest`, 59 tests, `make test`). Covers the sleep score,
  session/health alignment rules, snapshot cache behaviour, and schema/model
  drift. Tests use a throwaway SQLite file per test — never `bettertracker.db`.
- **Alembic migrations.** Baseline generated against a scratch database (the
  live DB already matched the models, so autogenerate would have produced an
  empty migration), then `alembic stamp head` on the real DB. Verified a fresh
  `alembic upgrade head` reproduces the schema exactly.
  Commands: `make migrate`, `make revision m="..."`, `make migration-status`.
- **`synced_at` on `health_snapshots`** + `get_or_refresh_snapshot()`. The
  `/health/snapshot` endpoint now refetches from Google only when the stored row
  is older than `SNAPSHOT_MAX_AGE_MINUTES` (default 60), making it cheap enough
  to call on every page load: ~2ms cached vs ~1.5s when it hits the API.
  `?force=true` bypasses the TTL.
- **Manual refresh button + freshness indicator** in the dashboard ("Updated 3
  min ago ↻"), wired to `?force=true`.
- **Structured logging** replacing 8 server-side `print()` calls, with
  `LOG_LEVEL` config. Health-sync failures log a full traceback via
  `logger.exception` — a silent failure there is how 12 days of data went
  missing. The three CLI scripts keep `print()`; that's their user interface.
- `is_competitive` exposed in `GameSessionResponse` / `ActiveSessionResponse`
  and the matching frontend types. It's the project's central variable and was
  unreachable from the UI.

### Fixed
- **`/steam/games` returned 500.** `GameDetails` declared `name` while
  `GameCache` stores `game_name`; with `from_attributes` the mismatch only
  surfaced at response time.
- **`Query(default=date.today())` on four endpoints.** Default arguments are
  evaluated once at import, so a long-running server kept serving whatever day
  it started on.
- **Health sync never ran.** The loop slept *before* its first fetch, so a
  process restarting more often than the interval (i.e. `uvicorn --reload`
  during development) never reached a sync. Now runs at startup, then sleeps,
  with a guard that skips if `last_success_at` is recent so reload storms can't
  hammer the API.
- `_clear_reauth()` no longer stamps `last_success_at`. Exchanging a token isn't
  fetching data, and stamping it suppressed the first real sync after a reconnect.
- Sleep duration ring showed `2.4h` for a 6.4-hour night (`%` instead of `/`).

### Changed
- Dashboard heading shows `Today` / `Yesterday` / `Thu, Aug 20` for the day the
  data actually belongs to. Bare `new Date("2026-08-22")` parses as UTC and
  renders as the previous day in western timezones — dates are parsed with an
  explicit `T00:00:00`.
- Sleep duration ring reads as clock time (`6:24`) rather than a decimal.
- Auth indicator shows connection state only; data freshness moved next to the
  data it describes.
- Insight cards dim below 5 sample days and show per-row day counts and value
  ranges, so a mean over 2 days can't read as a finding.
- `create_all()` removed from app startup — Alembic owns the schema now. It only
  ever created missing *tables* and silently ignored new columns, which is why
  column changes had been hand-written `ALTER`s.

### Migrations
- `73692c27cbfc` baseline existing schema
- `9aebb1523448` add `synced_at` to `health_snapshots`

---

## 2026-08-09

### Added
- **Wind-down and late-night insights.** Sleep bucketed by how long before bed
  the last session ended, and late-night vs earlier vs no gaming.
  "Late" is measured against `LATE_NIGHT_HOUR` on the *gaming* day, so a session
  ending at 1am counts as late rather than as an early-morning session.
- `sleep_start` / `sleep_end` captured per night. The API returns UTC plus a
  separate offset (`04:07Z` with `-18000s` is **23:07 local the previous
  evening**); these are converted to naive local wall time so they're comparable
  with `GameSession.start_time`.
- Guards on the wind-down metric: negative gaps, gaps over 12h, and sessions
  over 12h are excluded. A failed Steam poll leaves a session open until polling
  recovers, inflating `end_time` — the exact field the gap is measured from.

### Fixed
- Google Health serializes int64 as JSON **strings**; numeric sleep fields are
  coerced rather than compared as ints (was a 500 on `/health/sleep`).

---

## 2026-08-06

### Added
- **Auth health tracking**: `needs_reauth`, `last_error`, `last_success_at` on
  `oauth_tokens`, plus `GET /auth/status` and `DELETE /auth/token`.
  `refresh_access_token` distinguishes `invalid_grant` (grant is dead, reconnect
  required) from transient network failures, which must not mark the user
  disconnected. Without this, a dead grant reported "Connected" indefinitely.
- Frontend auth indicator with three states: connected, reconnect-needed,
  never-connected. "Reconnect" is worded differently from "Connect" because it
  means data silently stopped updating.

---

## 2026-08-05

### Added
- **Personalized sleep score calibration** (`calibrate_sleep_baseline.py`).
  Each sub-metric is scored against the user's own 10th/90th percentiles rather
  than fixed thresholds, clamped to healthy-adult bounds so worsening habits
  can't lower the target. Fixed thresholds saturated badly — every night maxed
  quality and restoration, leaving the score a proxy for duration alone
  (mean 93.2, 9 nights pegged at 100). After recalibration: mean 78.5, sd 12.0,
  matching Google's published 72–83 range.
- Sleep-onset latency is **not** scored: the API reports
  `minutesToFallAsleep: 0` on every session for this device.

---

## 2026-07-06

### Added
- Sleep score modeled on Google Health's documented structure
  (duration 50 / quality 25 / restoration 25).
- Health snapshot persistence, OAuth token persistence with 401-refresh-retry,
  `/health/snapshots` history endpoint, backfill script.
- Insights aligned on two rules: a **gaming day** runs 4am–4am, and a session is
  joined to the **next morning's** snapshot (a snapshot dated D holds the sleep
  that ended that morning).
- React + Vite + Tailwind dashboard: metric rings, trend chart, comparison cards.

---

## 2026-06-28 → 2026-06-30

### Added
- Initial FastAPI backend, SQLAlchemy models, Steam polling task for game
  session tracking, and the manual game cache (genre + competitive flag).
