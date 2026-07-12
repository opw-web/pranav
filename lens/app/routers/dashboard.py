import asyncio

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user, get_scoped_session
from app.database import get_scoped_db
from app.services.analytics import safe_to_spend, spending_detective
from app.services.recurring import upcoming
from app.services.transactions import list_transactions
from app.templating import templates

router = APIRouter()


async def _scoped(user_id: str, fn, *args, **kwargs):
    """Run `fn(session, ...)` on its own RLS-scoped session/transaction (its own pooled
    connection, via get_scoped_db). A single SQLAlchemy AsyncSession is not safe for
    concurrent use, so independent queries that we want to run in parallel each get
    their own session rather than sharing one — cheap now that connections are pooled
    (see app/database.py), and each still runs `SET LOCAL ROLE` / `SET LOCAL
    request.jwt.claim.sub` exactly as get_scoped_db always has.

    Cleanup is explicit (anext + finally: aclose()) rather than `async for ... return`,
    which would abandon the generator mid-yield and leave the transaction
    COMMIT/ROLLBACK and connection release to depend on GC-triggered async-generator
    finalization. Each call owns its own generator, so if a sibling branch in an
    asyncio.gather raises, this branch's connection is still released deterministically
    by its own `finally` — nothing strands on another branch's failure."""
    gen = get_scoped_db(user_id)
    session = await anext(gen)
    try:
        return await fn(session, *args, **kwargs)
    finally:
        await gen.aclose()


@router.get("/")
async def dashboard(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    txn_count = (
        await db.execute(
            text("SELECT COUNT(*) FROM transactions WHERE user_id=:uid AND is_deleted=FALSE"),
            {"uid": user.id},
        )
    ).scalar()

    if not txn_count:
        # First-run empty state — never a blank grid (§4.6, Check 17)
        return templates.TemplateResponse(request, "dashboard.html", {"empty": True, "user": user})

    # These four are independent of each other's results — run concurrently. Three get
    # their own scoped session/connection (see _scoped above); the fourth reuses the
    # request's already-open `db` session instead of opening a 5th connection. That's
    # safe here because exactly one coroutine (this one) touches `db` — the other three
    # run on their own separate connections, so there's no concurrent use of a single
    # AsyncSession. This bounds peak per-request connections at 4 (1 open `db` + 3
    # `_scoped`) instead of 5, so two concurrent dashboard loads no longer exhaust a
    # pool_size=5/max_overflow=5 engine (see app/database.py).
    sts, detective, due, recent = await asyncio.gather(
        _scoped(user.id, safe_to_spend, user.id),
        _scoped(user.id, spending_detective, user.id),
        _scoped(user.id, upcoming, user.id, within_days=14),
        list_transactions(db, user.id, {}, limit=8),
    )

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"empty": False, "user": user, "sts": sts, "detective": detective, "upcoming": due, "recent": recent},
    )
