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

## 2026-09-19

### Added
- **Frontend app shell (Phase 1 of the Lumida-style dashboard).** The single
  centered `App.tsx` is now a routed multi-page app: a persistent sidebar
  (Overview → Dashboard; Tracking → Activity, Sleep, Recovery, Health, Weight,
  Games) with a responsive mobile drawer, a shared top bar (Google connection +
  now-playing), and a dark-first design system. Why dark is forced via a `.dark`
  class on `<html>` rather than `prefers-color-scheme`: the reference look is
  dark and should render regardless of the viewer's OS setting.
- New dependency **`react-router-dom`** for the sidebar routing.
- Design tokens (`--color-*`) in `index.css` via Tailwind v4 `@theme`, mirrored
  as hex in `src/lib/colors.ts` for SVG presentation attributes (where
  `var(--token)` does **not** resolve — the reason the two coexist).
- Reusable UI primitives: `ui/Card` + `Stat`, `ui/Section` + `PageHeader`,
  `ui/ComingSoon`; layout `Sidebar` / `AppLayout`; extracted `AuthIndicator`,
  `FreshnessAction`, and `lib/format` helpers.
- **Interactive charts (Phase 2).** New dependency **`recharts`** plus themed
  wrappers in `src/components/charts/` — `LineTrend`, `BarWeek`, and a shared
  `ChartTooltip` — giving hover tooltips, axes, and a grid. Chart "chrome"
  colors live in `charts/chartTheme.ts`, mirroring the `index.css` tokens (same
  reason as `lib/colors.ts`: Recharts sets SVG attributes, where `var(--token)`
  won't resolve).
- **Data-backed tabs (Phase 3).** Built the four tabs that have data:
  - **Sleep** — per-night breakdown (score + time-asleep rings, sleep window,
    and a proportional stage-composition bar via `StageBar`) with a night
    picker, plus duration/score `LineTrend`s and a 14-night stacked
    `StageTrend`. Honesty note: the stage view is proportional, **not** a
    time-ordered hypnogram — Google stores per-stage totals, not the segment
    timeline, so a real hypnogram is future backend work.
  - **Recovery** — resting-HR and breathing-rate KPIs (latest + 7-day avg) and
    trends.
  - **Health** — cross-metric KPI grid, all four trends, and a Google Health
    connection/source card.
  - **Games** — currently-playing banner, a sessions timeline, recently-played
    (proportional bars), and the gaming↔recovery correlation cards.
- Helpers: `lib/stats` (`mean`, `latestOf`), `lib/format` (`clockTime`,
  `formatHm`, `monthDay`), `stageColors`; `LineTrend` gained a `yAllowDecimals`
  option (off for hour-based axes).
- **Activity/weight/SpO₂ metrics (Phase 4 — backend expansion).** The daily
  snapshot now also pulls **steps**, **active minutes**, **blood-oxygen (SpO₂)**,
  and **body weight** from Google Health. New nullable columns on
  `health_snapshots` (`steps`, `active_minutes`, `spo2`, `weight_kg`), exposed on
  `HealthSnapshotResponse` and mirrored in `types.ts`. The exact API field names
  were verified against the live API and are locked in by `test_activity_metrics.py`:
  - `steps` → `steps` dailyRollUp, `rollupDataPoints[].steps.countSum` (JSON **string**, coerced).
  - `active_minutes` → `active-minutes` dailyRollUp, summed across
    `activeMinutes.activeMinutesRollupByActivityLevel[].activeMinutesSum` (strings).
  - `spo2` → `daily-oxygen-saturation` list, `dailyOxygenSaturation.averagePercentage`.
  - `weight_kg` → `weight` list filtered on `weight.sample_time.physical_time`
    (a *sample* type, so it filters on physical time, not a `date`), value from
    `weight.weightGrams` ÷ 1000, taking the day's latest reading.
  Each new metric is fetched behind `_try_metric`, which swallows a single
  endpoint's failure to `None` so it can't abort the whole snapshot (which also
  carries the critical sleep/HR data).
- **Activity** and **Weight** tabs now render real data (weekly step bars, step
  trend, active-minutes trend; weight KPIs + trend). **SpO₂** added to the
  Recovery and Health tabs. `LineTrend`/`BarWeek` gained a `yTickFormatter`
  (compact "4k" for step axes).

### Changed
- The original dashboard (rings, trends, gaming-vs-recovery insight cards) moved
  into the **Dashboard** route, reusing `MetricRing` and `ComparisonCard`. Trend
  charts now use the interactive `LineTrend`. Activity/Weight (pending the Phase
  4 backend expansion) still render a "coming soon" stub.
- The full set of gaming↔recovery correlation cards (wind-down, late-night, plus
  competitive-vs-casual) moved from the Dashboard to the **Games** tab; the
  Dashboard keeps one teaser card that links to Games.
- Frontend `HealthSnapshot` type gained `sleep_start` / `sleep_end` — the
  backend `HealthSnapshotResponse` already returned them, but `types.ts` had
  drifted and omitted them (needed for the sleep window).
- Breathing-rate ring ceiling raised 20 → 30 /min so a normal night no longer
  fills the ring completely.
- **Resting HR and Breathing rings are now inverted** (lower value = fuller
  ring), so "fuller = better" now holds for *every* ring on the Dashboard.
  `MetricRing` gained `min` + `invert` props (defaults keep the old
  `value/max` behavior, so the sleep-score/duration rings are untouched).
  Display-only healthy-adult anchors — full at the best end, empty at the
  worst, not touching stored data or the sleep score: **Resting HR** 50 → 90
  bpm, **Breathing** 12 → 22 /min (supersedes the 20 → 30 ceiling above). A
  missing value renders empty, not full.

### Fixed
- **Steam API key leaked into logs on request failure.** The key rides in the
  URL query string (`?key=...` — Steam has no header auth), and `requests`
  embeds the full failing URL in its exception message. That message reached
  the logs verbatim via the poller's `logger.warning("Steam polling failed: %s", e)`
  and via any `/steam/*` 500 traceback. Steam requests now go through
  `steam_service._get_json()`, which catches `requests.RequestException` and
  re-raises with the key scrubbed to `***REDACTED***` (`settings.redact_secrets`,
  the single source of truth for what counts as a secret). This is a
  prerequisite for running under launchd, which captures stdout/stderr to files.
  The key was **not** rotated — the project isn't exposed yet. Guarded by
  `tests/test_steam_service.py`.

### Removed
- Hand-rolled `components/TrendChart.tsx` (no axes/tooltips), replaced by the
  Recharts-based `charts/LineTrend`.

### Migrations
- `c7f3a9d21b84` — add `steps`, `active_minutes`, `spo2`, `weight_kg` to
  `health_snapshots` (all nullable). **Run `make migrate`** before starting the
  server after pulling. Existing rows keep NULL for these columns; only days
  refetched within `HEALTH_SYNC_WINDOW_DAYS` populate them going forward, so to
  fill history run the backfill with `--force`, e.g.
  `venv/bin/python backfill_health.py --start 2026-06-12 --force`
  (it already routes through `build_snapshot_data`, so it picks up the new
  metrics automatically).

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
