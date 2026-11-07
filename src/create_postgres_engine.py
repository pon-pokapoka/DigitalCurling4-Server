from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine

from src.load_secrets import (
    db_max_overflow,
    db_name,
    db_pool_size,
    host,
    password,
    port,
    user,
)

# URL.create escapes the password, which may hold characters a URL can't.
POSTGRES_DATABASE_URL = URL.create(
    "postgresql+asyncpg",
    username=user,
    password=password,
    host=host,
    port=int(port) if port else None,
    database=db_name,
)

engine = create_async_engine(
    POSTGRES_DATABASE_URL,
    pool_size=db_pool_size,
    max_overflow=db_max_overflow,
    # Replaces connections left dead by a Postgres restart.
    pool_pre_ping=True,
)
