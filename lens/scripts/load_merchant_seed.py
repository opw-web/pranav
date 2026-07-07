"""Load app/seeds/merchants_in.csv into the merchant_seed table (idempotent: clears then reloads)."""
import asyncio
import csv
import os
import sys

import asyncpg
from dotenv import load_dotenv

load_dotenv()

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "app", "seeds", "merchants_in.csv")


def _sync_dsn(database_url: str) -> str:
    return database_url.replace("postgresql+asyncpg://", "postgresql://")


async def main():
    database_url = os.environ["DATABASE_URL"]
    conn = await asyncpg.connect(dsn=_sync_dsn(database_url))
    try:
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = [(r["pattern"].strip().lower(), r["merchant_clean"].strip(), r["category_key"].strip()) for r in reader]

        await conn.execute("TRUNCATE merchant_seed RESTART IDENTITY")
        await conn.executemany(
            "INSERT INTO merchant_seed (pattern, merchant_clean, category_key) VALUES ($1, $2, $3)",
            rows,
        )
        print(f"Loaded {len(rows)} merchant seed rows.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
