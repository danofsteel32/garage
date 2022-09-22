import asyncio
import os
from pathlib import Path

import aiosqlite
import pytest
import pytest_asyncio

from garage.db import create_db


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def db_file():
    return "test.db"


@pytest.fixture(scope="session")
def schema():
    _file = Path(".") / "src" / "schema.sql"
    with open(_file, "r") as file:
        schema = file.read()
    return schema


@pytest_asyncio.fixture(scope="session")
async def database(db_file):
    await create_db(db_file)
    async with aiosqlite.connect(db_file) as db:
        await db.execute(
            "insert into readings (val, ts) values (100.0, current_timestamp)"
        )
        await db.commit()
    yield
    Path(db_file).unlink()


@pytest.fixture(scope="session")
def app(database, db_file):
    from garage.server import app
    app.db_file = db_file
    os.environ["GARAGE_API_KEY"] = "testkey"
    return app
