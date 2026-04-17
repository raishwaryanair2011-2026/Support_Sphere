"""
Run this once to add department column to users table.
Place in D:\support-portal-v2 and run:  python alembic_department_migration.py
"""
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(".env", override=True)
import aiosqlite

async def migrate():
    async with aiosqlite.connect("support.db") as db:
        # Check if column already exists
        cursor = await db.execute("PRAGMA table_info(users)")
        cols = [row[1] for row in await cursor.fetchall()]
        if "department" in cols:
            print("Column 'department' already exists — skipping.")
            return
        await db.execute("ALTER TABLE users ADD COLUMN department VARCHAR(60)")
        await db.commit()
        print("✅ Added 'department' column to users table.")

asyncio.run(migrate())