---
name: changelog
description: Record a significant code change in CHANGELOG.md, and check prior decisions before changing existing behaviour. Use after completing any change that alters behaviour, schema, configuration, or the API surface — new features or endpoints, bug fixes, migrations, renames, dependency additions, or changed defaults. Also use before modifying sleep scoring, session/health alignment, sync or cache timing, or auth state, and when the user asks what changed recently.
---

# Updating CHANGELOG.md

`CHANGELOG.md` lives at the repo root. It carries project memory across
sessions: chats don't share context, so this file is the only thing preventing
a later session from undoing a decision it can't see the reasoning for.

## Before changing existing behaviour

Read the **"Deliberate decisions — do not revert"** table at the top of
`CHANGELOG.md` first. It lists choices that look like bugs or oversights but
are intentional — several were reached only after the obvious version failed in
practice. If a change contradicts one, either don't make it, or update that row
in the same commit explaining what changed.

## When to add an entry

Add one when the change affects **behaviour, schema, configuration, or the API
surface**:

- a new endpoint, feature, or script
- a bug fix (especially one whose cause was non-obvious)
- an Alembic migration, or any change to a model
- a new or renamed config setting, or a changed default
- a new dependency
- a change to a rule the project's conclusions depend on — scoring weights,
  the gaming-day boundary, cache windows, sample-size thresholds

**Do not** add an entry for: comment or docstring edits, formatting, renaming a
local variable, adding a test for existing behaviour that already had an entry,
or work-in-progress that doesn't run yet. A changelog that records everything
gets skimmed and stops being read.

If unsure, ask: *would someone debugging this in three months want to know?*

## How to write the entry

Append under a `## YYYY-MM-DD` heading for today. **Reuse today's section if it
already exists** — never create a second one for the same date. Within it, use
`### Added`, `### Fixed`, `### Changed`, `### Removed`, `### Migrations`.

Each entry states what changed **and why**. The "why" is the part worth writing:

> - **Health sync never ran.** The loop slept *before* its first fetch, so a
>   process restarting more often than the interval (i.e. `uvicorn --reload`)
>   never reached a sync.

not:

> - Fixed the health sync.

Specifics that make an entry useful later:

- **Name the real cause**, not the symptom. "`%` instead of `/`" beats "wrong
  number displayed."
- **Include numbers** when a change was calibrated against data — before/after
  means, thresholds, timings. These justify constants that otherwise look
  arbitrary.
- **Quote exact identifiers** — column names, config keys, revision IDs — so
  the entry is greppable.
- **Flag manual steps loudly.** A migration that needs `make migrate`, a script
  that must be re-run, a required re-auth. Forgetting one breaks the next run.
- Record decisions that were **deliberately not** taken when they'd otherwise
  look like oversights (e.g. "latency is not scored: the API always reports 0").

## Migrations

Any Alembic revision gets a `### Migrations` line with its revision ID and
description, plus a note in the relevant entry that `make migrate` is required.

## Process

1. Read `CHANGELOG.md` to match existing tone and check for today's section.
2. Add the entry in the right category.
3. Keep newest-first ordering; do not restructure past entries.
4. Mention to the user that you updated it — don't do it silently.
