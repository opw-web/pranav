import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_or_create_tag(session: AsyncSession, user_id: str, name: str) -> str:
    name = name.strip()
    row = (
        await session.execute(
            text("SELECT id FROM tags WHERE user_id = :uid AND lower(name) = lower(:name)"),
            {"uid": user_id, "name": name},
        )
    ).first()
    if row:
        return str(row[0])
    tag_id = str(uuid.uuid4())
    await session.execute(
        text("INSERT INTO tags (id, user_id, name) VALUES (:id, :uid, :name)"),
        {"id": tag_id, "uid": user_id, "name": name},
    )
    return tag_id


async def set_transaction_tags(session: AsyncSession, user_id: str, txn_id: str, tag_names: list[str]):
    await session.execute(
        text(
            "DELETE FROM transaction_tags WHERE transaction_id = :tid AND EXISTS "
            "(SELECT 1 FROM transactions t WHERE t.id = :tid AND t.user_id = :uid)"
        ),
        {"tid": txn_id, "uid": user_id},
    )
    for name in tag_names:
        name = name.strip()
        if not name:
            continue
        tag_id = await get_or_create_tag(session, user_id, name)
        await session.execute(
            text("INSERT INTO transaction_tags (transaction_id, tag_id) VALUES (:tid, :tagid) ON CONFLICT DO NOTHING"),
            {"tid": txn_id, "tagid": tag_id},
        )


async def get_transaction_tags(session: AsyncSession, user_id: str, txn_id: str):
    result = await session.execute(
        text(
            "SELECT t.id, t.name FROM tags t JOIN transaction_tags tt ON tt.tag_id = t.id "
            "WHERE tt.transaction_id = :tid AND t.user_id = :uid ORDER BY t.name"
        ),
        {"tid": txn_id, "uid": user_id},
    )
    return result.mappings().all()
