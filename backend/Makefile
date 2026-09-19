run:
	uvicorn main:app --reload

install:
	pip install -r requirements.txt

test:
	pytest

freeze:
	pip freeze > requirements.txt

# --- Database migrations (Alembic) ---

# Apply any pending migrations. Run after pulling changes, before `make run`.
migrate:
	alembic upgrade head

# Generate a migration from model changes: make revision m="add synced_at"
# ALWAYS read the generated file before applying — autogenerate misses some
# changes (renames look like drop+add, and it can't see data migrations).
revision:
	alembic revision --autogenerate -m "$(m)"

# Which revision the database is currently at.
migration-status:
	alembic current

# Undo the most recent migration.
downgrade:
	alembic downgrade -1

# --- launchd session-capture agent (macOS) ---
# Keeps the backend (and its Steam poller) running at login. See
# ../scripts/launchd/README.md. Note: the agent owns port 8000, so run
# `make agent-stop` before `make run` and `make agent-start` after.

AGENT_DIR = ../scripts/launchd
AGENT_LABEL = com.bettertracker.backend
AGENT_DOMAIN = gui/$(shell id -u)
AGENT_LOG = $(HOME)/Library/Logs/bettertracker/backend.log

agent-install:
	$(AGENT_DIR)/install-agent.sh

agent-uninstall:
	$(AGENT_DIR)/uninstall-agent.sh

agent-status:
	launchctl print $(AGENT_DOMAIN)/$(AGENT_LABEL)

agent-logs:
	tail -f $(AGENT_LOG)

agent-restart:
	launchctl kickstart -k $(AGENT_DOMAIN)/$(AGENT_LABEL)

agent-stop:
	launchctl bootout $(AGENT_DOMAIN)/$(AGENT_LABEL)

agent-start:
	launchctl bootstrap $(AGENT_DOMAIN) $(HOME)/Library/LaunchAgents/$(AGENT_LABEL).plist
