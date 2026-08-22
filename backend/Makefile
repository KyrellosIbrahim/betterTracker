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
