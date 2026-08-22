import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Alembic runs this file directly, so the app package isn't on sys.path yet.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings  # noqa: E402
from database import Base  # noqa: E402
import models  # noqa: E402,F401  (registers every model on Base.metadata)

config = context.config

# One source of truth for the DB URL: config.py / the DATABASE_URL env var,
# rather than duplicating it in alembic.ini. ALEMBIC_DATABASE_URL can override
# it when pointing at a scratch database.
config.set_main_option("sqlalchemy.url", os.environ.get("ALEMBIC_DATABASE_URL", settings.DATABASE_URL))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# SQLite can't ALTER most things in place, so Alembic has to rebuild the table
# (create new, copy, drop, rename). Without batch mode, dropping or altering a
# column fails outright on SQLite.
BATCH_MODE = settings.DATABASE_URL.startswith("sqlite")


def run_migrations_offline() -> None:
    """Run migrations without a DBAPI connection, emitting SQL."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=BATCH_MODE,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=BATCH_MODE,
            # Surface column type changes too, not just added/dropped columns.
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
