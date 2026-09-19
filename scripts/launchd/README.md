# Always-on Steam session capture (macOS launchd)

Steam sessions are only recorded while the backend is running, and they **can't
be backfilled** — Steam exposes aggregate playtime, never timestamps. This
LaunchAgent keeps `uvicorn` running so capture doesn't depend on a terminal
being open: it starts at login, restarts on crash, and logs to a file.

Scope is the **backend only** (`127.0.0.1:8000`). Start the Vite dashboard by
hand (`npm run dev`) when you want to look at it.

## Install

From `backend/`:

```bash
make agent-install
```

This renders `com.bettertracker.backend.plist` into `~/Library/LaunchAgents/`
with your absolute paths, loads it, and starts it. It's idempotent — re-run it
after pulling changes (it reloads the agent; the wrapper also runs
`alembic upgrade head` on each start).

Requires the backend venv to exist first (`make install`).

## Manage

From `backend/`:

| Command | What it does |
|---|---|
| `make agent-status`  | `launchctl print` — shows running state + last exit code |
| `make agent-logs`    | `tail -f ~/Library/Logs/bettertracker/backend.log` |
| `make agent-restart` | restart now (`launchctl kickstart -k`) |
| `make agent-stop`    | stop + unload (until re-started or next login) |
| `make agent-start`   | load + start again |
| `make agent-uninstall` | stop and remove the plist (logs are kept) |

## Developing while the agent runs

The agent owns port **8000**, and SQLite doesn't like two writers, so the dev
server (`make run`, which uses `--reload`) will conflict. Toggle around it:

```bash
make agent-stop     # free the port + DB
make run            # develop with hot reload
make agent-start    # resume capture when done
```

## Notes

- It's a **LaunchAgent**, so it runs while you're logged in (fine for a personal
  laptop). It uses `backend/.env` and `backend/bettertracker.db` directly — no
  secrets are copied into the plist.
- Logs are safe on disk: the Steam API key is redacted before logging.
- Unrelated but complementary (not handled here): move the Google OAuth consent
  screen to "In production" so refresh tokens stop expiring ~weekly.
