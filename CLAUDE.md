# BetterTracker

Personal dashboard correlating Google Health data (sleep, resting HR, breathing
rate) with Steam gaming sessions. The question it exists to answer: **does
competitive gaming hurt my recovery?**

## Read this first

**`ROADMAP.md`** has the current state and the prioritized next steps. The short
version: the pipeline is complete, but there are 72 days of health data against
3 days of gaming data, so every insight is starved. Session capture reliability
beats any new feature — health data can be refetched, Steam sessions cannot.

**`CHANGELOG.md` has a "Deliberate decisions — do not revert" table.** Several
things in this codebase look like bugs or oversights and are not — they were
arrived at after the obvious version failed. Check that table before changing:

- the sleep score, its weights, or its calibration
- the gaming-day boundary or the session ↔ snapshot join
- snapshot caching / sync timing
- auth state (`connected`, `needs_reauth`)
- anything schema-related

If you change one of those decisions anyway, update the table in the same commit.

## Layout

```
backend/    FastAPI + SQLAlchemy + SQLite. Run from this directory.
  models/       ORM. Every model must be imported in models/__init__.py
                or Alembic autogenerate won't see it.
  schemas/      Pydantic. Field names must match model attributes when
                from_attributes is set — a mismatch is a 500 at response time,
                invisible to type checking. tests/test_schemas.py guards this.
  services/     Business logic. Returns plain dicts, not schemas.
  controllers/  Routes. Thin.
  alembic/      Migrations. Owns the schema; there is no create_all().
frontend/   React + Vite + Tailwind v4. src/api/types.ts mirrors the Pydantic
            schemas — keep them in sync.
```

Note: `fitbit_service.py` / `fitbit_controller.py` / `schemas/fitbit.py` talk to
**Google Health**, not Fitbit. The names are stale from the API migration.

## Commands

Run from `backend/`:

```bash
make test              # pytest — run before and after any change
make migrate           # alembic upgrade head — after pulling, before running
make revision m="..."  # autogenerate a migration; ALWAYS read it before applying
make run               # uvicorn --reload
```

Frontend: `npm run dev` / `npm run build` from `frontend/`.

## Conventions

- **Update `CHANGELOG.md`** for any change to behaviour, schema, config, or the
  API surface. The `changelog` skill in `.claude/skills/` covers what counts and
  how to write the entry. Not for comments, formatting, or local renames.
- Server code uses `logging`; the CLI scripts use `print()` on purpose.
- Tests use a throwaway SQLite file per test. Never point tests at
  `bettertracker.db` — it holds real health history that cannot be
  re-collected for game sessions.

## Gotchas that have already cost time

- Google serializes int64 as JSON **strings** — coerce numeric API fields.
- Sleep timestamps are UTC **plus a separate offset**; convert to naive local
  before comparing with `GameSession.start_time` (which is `datetime.now()`).
- `Query(default=date.today())` freezes "today" at import. Default to `None`
  and resolve inside the handler.
- Steam sessions only record while the backend is running, and **cannot be
  backfilled** — Steam exposes aggregate playtime, not timestamps. Health data
  can always be re-fetched; session gaps are permanent.
- If the OAuth consent screen is in "Testing" status, Google expires refresh
  tokens after 7 days.
