from dataclasses import dataclass
from datetime import datetime

import aiosqlite

DIST_CUTOFF = 70  # inches


@dataclass(slots=True, frozen=True)
class Status:
    """Represents the state of the garage for rendering in template."""

    dist: float
    timestamp: datetime

    @property
    def color(self) -> str:
        if self.dist > DIST_CUTOFF:
            return "green"
        return "red"

    @property
    def state(self) -> str:
        if self.dist > DIST_CUTOFF:
            return "Closed"
        return "OPEN!"

    @property
    def sensor_down(self) -> bool:
        status_age = datetime.now() - self.timestamp
        if status_age.seconds > 10:
            return True
        return False

    @classmethod
    def new(cls, dist: float) -> "Status":
        if not isinstance(dist, float):
            raise ValueError(f"dist must be of type float, not {type(dist)}")
        return cls(dist, datetime.now())


async def get_last_status(dbfile: str = "readings.db") -> Status:
    # TODO: handle db no exist
    async with aiosqlite.connect(dbfile) as db:
        cursor = await db.execute(
            "select val, ts from readings order by ts desc limit 1"
        )
        row = await cursor.fetchone()
        if not row:
            raise ValueError("No rows to fetch")
        dist, ts = row
        status = Status(dist=dist, timestamp=datetime.fromisoformat(ts))
    return status


async def save_status(status: Status, dbfile: str = "readings.db") -> None:
    # TODO: handle db no exist
    async with aiosqlite.connect(dbfile) as db:
        await db.execute(
            "insert into readings (val, ts) values (?, ?)",
            (status.dist, status.timestamp),
        )
        await db.commit()
