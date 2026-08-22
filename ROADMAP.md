# Roadmap

Where the project stands and what to do next. Read alongside `CLAUDE.md` and the
"Deliberate decisions" table in `CHANGELOG.md`.

---

## Where it stands (2026-08-22)

The pipeline is **finished end to end**: OAuth with dead-grant detection, hourly
health sync, per-day snapshot caching, Steam session tracking, the calibrated
sleep score, the alignment rules, four insight endpoints, a working dashboard,
59 tests, and Alembic migrations.

The data is **not**:

| | |
|---|---|
| Health snapshots | **72** (Jun 12 → Aug 22, no gaps) |
| Game sessions | **3** |
| Distinct gaming days | **3** (Aug 4, 7, 8) |
| Competitive days with a recovery morning | **1** |
| Wind-down buckets with any data | **1 of 3** (n=2) |

Every insight card is dimmed because every bucket is below the 5-day threshold.

**The bottleneck is data collection, not code.** More features will not make the
dashboard say anything. This should drive the ordering below.

The asymmetry that matters: **health data can always be refetched from Google;
Steam sessions cannot be backfilled at all.** Steam only exposes aggregate
playtime, never timestamps. Every day the backend isn't running is a gaming day
that is permanently, unrecoverably lost. Between Aug 10–22 the backend was up
but the sync was broken — health data was recovered, sessions were not.

---

## Phase 0 — Stop losing data (do this first)

Nothing else is worth doing until session capture is reliable.

1. **Keep the backend running: launchd agent.**
   Sessions are only recorded while `uvicorn` is up. A `~/Library/LaunchAgents`
   plist with `KeepAlive` and `RunAtLoad`, logging to a file. This is the single
   highest-value item in this document — it's the difference between collecting
   data and not.

2. **Rotate the Steam API key, and scrub it from logs.**
   `config.py` puts the key in the URL, so `requests` includes it in every
   connection-error message. This was tolerable when errors scrolled past in a
   terminal; once launchd writes logs to a file it's a credential sitting on
   disk. A redaction filter on the logging config is the fix. Rotate at
   https://steamcommunity.com/dev/apikey.

3. **Move the Google OAuth consent screen to "In production."**
   Refresh tokens for apps in "Testing" expire after 7 days — the likely cause
   of the Aug 9 grant death. In production they persist. Until then expect to
   reconnect roughly weekly (the dashboard will say "Reconnect Google Health").

---

## Phase 1 — Make captured sessions trustworthy

Do these once sessions are actually accumulating.

4. **Handle idle/AFK sessions.** Steam reports "in game" for a launched game
   whether or not anyone is playing. Real evidence: the Aug 8 Brawlhalla session
   ran until 02:23, but the watch logged sleep starting 00:55 — the game was
   open for 90 minutes after sleep began. That corrupts session duration and the
   wind-down gap, which is measured from `end_time`.
   Options: cap a session at the point sleep starts, or treat sessions longer
   than some threshold as unreliable rather than real.

5. **Surface dropped sessions instead of silently excluding them.**
   `MAX_PLAUSIBLE_SESSION_MINUTES` currently discards outage-inflated sessions
   with no trace. Log them, or flag the row, so the exclusion is visible.

---

## Phase 2 — Wait, and watch the sample sizes

This phase is mostly calendar time, not work.

The insight cards need **n ≥ 5 recovery days per bucket** to stop being dimmed,
and realistically more like 10–15 per bucket before a difference in means is
worth believing. With reliable capture and a normal mix of competitive and
casual play, that's roughly **3–6 weeks**.

Check progress with:

```bash
curl -s localhost:8000/insights/sleep-impact-competitive
```

Watch `sample_days` per bucket. When competitive and casual are both ≥5, the
dashboard starts being informative.

---

## Phase 3 — Finish the dashboard

Worth doing during Phase 2, since by the end there'll be data to display. The
`TODO` markers in `frontend/src/App.tsx` mark the spots.

6. **Sleep-impact card** — three buckets, competitive vs casual-only vs
   no-gaming. `getSleepImpactCompetitive()` already exists in the client and is
   unused. Pass `sampleDays` and `spread` like the existing cards.
7. **Genre breakdown table** — `getSleepImpactByGenre()` also already exists.
8. **Session timeline** for a day, using `getSessions(date)`.
9. **Session length vs next-day sleep score** scatter — the one view that shows
   dose-response rather than a bucketed average.
10. More rings: deep sleep against a 90-minute goal, resting HR inverted.
    `MetricRing` takes a `display` prop, so `1:23` formatting is available.

---

## Phase 4 — Analysis maturity (once data exists)

11. **Exercise as a confounder.** This is the biggest threat to the project's
    conclusion. Workout days independently affect sleep and resting HR, so
    without it, exercise can masquerade as a gaming effect — or mask one.
    `fetch_exercise()` already exists in `fitbit_service.py` and is unused.
    Adding it means snapshot columns + a migration + backfill with `--force`.
12. **Weekly rollups** — total playtime vs average sleep score by week. Weekly
    aggregation is less noisy than per-day and may show a signal the daily view
    can't.
13. **Export** — CSV of the joined dataset, so analysis can happen outside the app.
14. **Recalibrate the sleep baseline** every few months:
    `venv/bin/python calibrate_sleep_baseline.py --start <date> --rescore`,
    then restart the server (anchors are cached in-process).

---

## Phase 5 — Deferred cleanups

Known, deliberately postponed. None affect behaviour.

15. Rename `fitbit_service.py` / `fitbit_controller.py` / `schemas/fitbit.py` →
    `google_health_*`. They haven't talked to Fitbit since the API migration.
16. Unify config units — `HEALTH_SYNC_INTERVAL` is seconds while
    `SNAPSHOT_MAX_AGE_MINUTES` is minutes, and they govern related concerns.
17. `_local_time(interval, time_key, offset_key)` ignores `offset_key`; it works
    via `.astimezone()`, which is correct only while the server's timezone
    matches where you sleep. Either use the parameter or drop it.

---

## Before changing anything

Read the **"Deliberate decisions — do not revert"** table in `CHANGELOG.md`.
Several things here look like bugs and are not. Run `make test` before and after.
Update `CHANGELOG.md` for anything that changes behaviour, schema, config, or
the API surface.
