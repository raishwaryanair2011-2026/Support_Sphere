"""
Alembic migration environment.
Automatically detects SQLite vs PostgreSQL and uses the appropriate connection strategy.
"""
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import get_settings
from app.db.base import Base
import app.models  # noqa: F401 — registers all ORM models

settings = get_settings()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use the app's DATABASE_URL
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata

IS_SQLITE = settings.DATABASE_URL.startswith("sqlite")


# ── Offline (generate SQL without a live DB) ──────────────────────────────────
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=IS_SQLITE,  # SQLite requires batch mode for ALTER TABLE
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online: SQLite (sync — aiosqlite not needed for migrations) ───────────────
def run_migrations_sqlite() -> None:
    # Strip the async prefix so the sync engine can connect directly
    sync_url = settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite")

    sync_config = config.get_section(config.config_ini_section, {})
    sync_config["sqlalchemy.url"] = sync_url

    connectable = engine_from_config(
        sync_config,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True,  # required for SQLite ALTER TABLE support
        )
        with context.begin_transaction():
            context.run_migrations()


# ── Online: PostgreSQL (async) ────────────────────────────────────────────────
def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    if IS_SQLITE:
        run_migrations_sqlite()
    else:
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()