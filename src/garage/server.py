import asyncio
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import aiosqlite
from quart import Quart, abort, jsonify, make_response, render_template, request
from quart.helpers import stream_with_context

from .db import create_db
from .status import Status, get_last_status, save_status

app = Quart(__name__)
app.clients = set()
app.db_file = "readings.db"


@dataclass(slots=True)
class ServerSentEvent:
    data: str
    event: str | None = None
    id: int | None = None
    retry: int | None = None

    def encode(self) -> bytes:
        # remove newlines in case data is a rendered template
        self.data = self.data.replace("\n", "")
        message = f"data: {self.data}"
        if self.event is not None:
            message = f"{message}\nevent: {self.event}"
        if self.id is not None:
            message = f"{message}\nid: {self.id}"
        if self.retry is not None:
            message = f"{message}\nretry: {self.retry}"
        message = f"{message}\r\n\r\n"
        return message.encode("utf-8")


@app.before_serving
async def ensure_db_exists():
    if not Path(app.db_file).exists():
        await create_db(app.db_file)


@app.route("/garage/status", methods=["GET"])
async def dashboard():
    """Get the last reading from db and use it to render the initial page."""
    try:
        status = await get_last_status(app.db_file)
    except (aiosqlite.Error, ValueError) as ex:
        app.logger.warning(f"Could not get last status {ex}")
        status = Status(0.0, datetime(1900, 1, 1))
    return await render_template("dashboard.html", status=status)


@app.route("/garage/status", methods=["POST"])
async def status():
    data = await request.get_json()

    api_key = request.headers.get("X-Api-Key", False)
    if not api_key:
        abort(401)
    if api_key != os.getenv("GARAGE_API_KEY", True):
        abort(401)

    try:
        status = Status.new(data["message"])
    except ValueError:
        return jsonify({"message": "message field not provided or incorrect type"}), 400

    try:
        await save_status(status, app.db_file)
    except aiosqlite.Error as ex:
        app.logger.warning(f"Could not save status, {ex}")

    for queue in app.clients:
        if queue.full():
            app.clients.remove(queue)
            app.logger.info("Removing Client because queue full")
            continue
        await queue.put(data["message"])
    return jsonify(True)


@app.route("/garage/sse")
async def sse():
    """Broadcasts any events put into the clients queues by the status() function."""

    if "text/event-stream" not in request.accept_mimetypes:
        abort(400)

    app.logger.info("called")
    queue: asyncio.Queue[float] = asyncio.Queue(10)
    app.clients.add(queue)
    app.logger.info("Client connected")

    @stream_with_context
    async def send_events():
        while True:
            try:
                data = await queue.get()
                status = Status.new(data)
                html = await render_template("status_partial.jinja", status=status)
                event = ServerSentEvent(html, event="StatusUpdate")
                yield event.encode()
            except asyncio.CancelledError:
                app.clients.remove(queue)
                app.logger.info("Client disconnected")
                break

    response = await make_response(
        send_events(),
        {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Transfer-Encoding": "chunked",
        },
    )
    response.timeout = None
    return response
