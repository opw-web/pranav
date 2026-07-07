import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings

# Supabase's direct DB host (db.<ref>.supabase.co) is IPv6-only on newer projects and
# flaky over IPv6 on many networks; the Supavisor pooler gives a stable IPv4 endpoint and
# is what Vercel serverless needs anyway (§2.7). Transaction-mode pooling requires:
#  - NullPool: Supavisor already pools; a second client-side pool fights it.
#  - statement_cache_size=0 + unique prepared-statement names: pooled server connections
#    rotate between transactions, so cached prepared statements would reference the wrong one.
_connect_args = {
    "statement_cache_size": 0,
    "prepared_statement_name_func": lambda: f"__asyncpg_{uuid.uuid4()}__",
    "server_settings": {"application_name": "lens"},
}

engine = create_async_engine(settings.database_url, poolclass=NullPool, connect_args=_connect_args)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """Plain session, no RLS context. Only for admin/global reads (e.g. merchant_seed)."""
    async with async_session() as session:
        yield session


async def get_scoped_db(user_id: str):
    """
    Session scoped to a specific user for the duration of one transaction.

    Our DATABASE_URL connects as the `postgres` role, which has BYPASSRLS —
    RLS would silently no-op if we ran queries as-is. To make RLS a REAL
    second layer (not just app-level filtering), every request-scoped query
    runs inside a transaction as the `authenticated` role with the same
    `request.jwt.claim.sub` GUC that Supabase's `auth.uid()` reads, so
    Postgres enforces the same policies a PostgREST call would.
    """
    # SET does not support bind parameters over the wire protocol, so we validate
    # the value is a genuine UUID first and interpolate that (not raw user input).
    safe_uid = str(uuid.UUID(str(user_id)))

    async with async_session() as session:
        async with session.begin():
            await session.execute(text("SET LOCAL ROLE authenticated"))
            await session.execute(text(f"SET LOCAL request.jwt.claim.sub = '{safe_uid}'"))
            yield session
