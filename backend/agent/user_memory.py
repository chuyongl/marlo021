"""
Migration: add user_memory column to businesses table

Run once:
    python backend/migrations/add_user_memory.py

Or add this to your startup auto-migration if you have one.
"""

import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")

import asyncpg


async def run_migration():
    db_url = os.getenv("DATABASE_URL", "").replace("+asyncpg", "").replace("postgresql://", "postgres://")

    conn = await asyncpg.connect(db_url)
    try:
        # Check if column already exists
        exists = await conn.fetchval("""
            SELECT COUNT(*) FROM information_schema.columns
            WHERE table_name = 'businesses' AND column_name = 'user_memory'
        """)

        if exists:
            print("✅ user_memory column already exists, skipping.")
            return

        # Add the column
        await conn.execute("""
            ALTER TABLE businesses
            ADD COLUMN user_memory JSONB DEFAULT NULL
        """)
        print("✅ Added user_memory column to businesses table.")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migration())