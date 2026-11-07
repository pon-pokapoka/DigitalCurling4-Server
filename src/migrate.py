"""Bring the database up to date, then create the users in DC_USERS.

Applies postgres/init/*.sql, each once, in name order. Run before the server
starts: as an init container on Kubernetes, ahead of fastapi in Compose.
Replicas may run it together: an advisory lock makes them take turns.

    python -m src.migrate

DC_USERS is optional, a JSON object of username to password. Passwords of
existing users are replaced, so it can also change them.
"""

import asyncio
import json
import logging
import os
from pathlib import Path

import asyncpg

from src.authentication.basic_authentication_crud import CreateAuthentication
from src.db import Session
from src.load_secrets import db_name, host, password, port, user

# Arbitrary, but must stay distinct from src/main.py's SEED_LOCK_ID.
MIGRATION_LOCK_ID = 4_000_001
MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "postgres" / "init"
# Databases set up before this tracking existed already hold these. The files
# aren't safe to repeat: ALTER TABLE ... ADD CONSTRAINT fails the second time.
BASELINE = ("01_init.sql", "02_init.sql")

CONNECT_ATTEMPTS = 30
CONNECT_DELAY_SECONDS = 2


async def connect() -> asyncpg.Connection:
    """Connect, waiting for a database that's still starting."""
    for attempt in range(1, CONNECT_ATTEMPTS + 1):
        try:
            return await asyncpg.connect(
                user=user, password=password, host=host, port=port, database=db_name
            )
        except (OSError, asyncpg.CannotConnectNowError) as e:
            if attempt == CONNECT_ATTEMPTS:
                raise
            logging.info("Waiting for Postgres (%s/%s): %s", attempt, CONNECT_ATTEMPTS, e)
            await asyncio.sleep(CONNECT_DELAY_SECONDS)
    raise AssertionError("unreachable")


async def apply_migrations(connection: asyncpg.Connection) -> None:
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename VARCHAR PRIMARY KEY,
            applied_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """
    )
    applied = {
        row["filename"]
        for row in await connection.fetch("SELECT filename FROM schema_migrations")
    }

    if await connection.fetchval("SELECT to_regclass('public.match_data')") is not None:
        for filename in BASELINE:
            if filename not in applied:
                await connection.execute(
                    "INSERT INTO schema_migrations (filename) VALUES ($1)", filename
                )
                applied.add(filename)

    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if path.name in applied:
            continue
        logging.info("Applying %s", path.name)
        async with connection.transaction():
            await connection.execute(path.read_text(encoding="utf-8"))
            await connection.execute(
                "INSERT INTO schema_migrations (filename) VALUES ($1)", path.name
            )


async def migrate() -> None:
    connection = await connect()
    try:
        await connection.execute("SELECT pg_advisory_lock($1)", MIGRATION_LOCK_ID)
        await apply_migrations(connection)
    finally:
        # Closing the connection also releases the lock.
        await connection.close()


def parse_users(raw: str | None) -> dict[str, str]:
    """Read DC_USERS. Errors don't quote it: it holds passwords."""
    if not raw:
        return {}
    try:
        users = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError("DC_USERS must be a JSON object") from None
    valid = isinstance(users, dict) and all(
        name and isinstance(secret, str) and secret for name, secret in users.items()
    )
    if not valid:
        raise ValueError("DC_USERS must map each username to a non-empty password")
    return users


async def create_users(users: dict[str, str]) -> None:
    async with Session() as session:
        for username, secret in users.items():
            await CreateAuthentication.create_user_data(username, secret, session)
            logging.info("Created or updated user %s", username)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    # Parsed first, so a bad secret fails before anything changes.
    users = parse_users(os.getenv("DC_USERS"))
    await migrate()
    await create_users(users)


if __name__ == "__main__":
    asyncio.run(main())
