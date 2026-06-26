from __future__ import annotations

import asyncio
import importlib
from datetime import datetime, timezone
from typing import Any

import live_logic


RUNTIME_TICK_SECONDS = 2
TASK: asyncio.Task | None = None
RUNNING = False
SUBSCRIBERS: set[asyncio.Queue] = set()


def logic():
    return importlib.reload(live_logic)


async def broadcast(message: dict[str, Any]) -> None:
    stale: list[asyncio.Queue] = []
    for queue in SUBSCRIBERS:
        try:
            queue.put_nowait(message)
        except asyncio.QueueFull:
            stale.append(queue)

    for queue in stale:
        SUBSCRIBERS.discard(queue)


async def runtime_loop() -> None:
    global RUNNING
    RUNNING = True

    while RUNNING:
        update = logic().tick_world()
        await broadcast(update["snapshot"])
        await asyncio.sleep(RUNTIME_TICK_SECONDS)


async def start_runtime() -> dict[str, Any]:
    global TASK, RUNNING

    if TASK and not TASK.done():
        return status()

    RUNNING = True
    TASK = asyncio.create_task(runtime_loop())
    return status()


async def stop_runtime() -> dict[str, Any]:
    global RUNNING, TASK
    RUNNING = False

    if TASK:
        await asyncio.sleep(0)
        if TASK.done():
            TASK = None

    return status()


def subscribe() -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue(maxsize=4)
    SUBSCRIBERS.add(queue)
    return queue


def unsubscribe(queue: asyncio.Queue) -> None:
    SUBSCRIBERS.discard(queue)


async def push_current_state(queue: asyncio.Queue) -> None:
    await queue.put(logic().build_snapshot())


def status() -> dict[str, Any]:
    return {
        "running": RUNNING,
        "task_active": bool(TASK and not TASK.done()),
        "subscribers": len(SUBSCRIBERS),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        **logic().get_state(),
    }
