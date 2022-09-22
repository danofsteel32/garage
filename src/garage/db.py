import aiosqlite

SCHEMA = """
create table if not exists readings (
    val numeric,
    ts timestamp
);
"""


async def create_db(db_file: str = "readings.db"):
    async with aiosqlite.connect(db_file) as db:
        await db.execute(SCHEMA)
        await db.commit()
