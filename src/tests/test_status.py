from datetime import datetime

import pytest

from garage.status import Status, get_last_status, save_status


def test_garage_open():
    status = Status.new(100.0)
    assert status.color == "green"
    assert status.state == "Closed"


def test_garage_closed():
    status = Status.new(50.0)
    assert status.color == "red"
    assert status.state == "OPEN!"


def test_sensor_down():
    up = Status.new(50.0)
    down = Status(50.0, datetime(1900, 1, 1))
    assert not up.sensor_down
    assert down.sensor_down


@pytest.mark.asyncio
async def test_get_last_status(database, db_file):
    status = await get_last_status(db_file)
    assert isinstance(status, Status)


@pytest.mark.asyncio
async def test_save_status(database, db_file):
    try:
        await save_status(Status.new(50.0), db_file)
    except Exception as ex:
        print(ex)
        pytest.fail()
