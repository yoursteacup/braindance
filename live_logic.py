from __future__ import annotations

from typing import Any

from simulation.engine import TickEngine, create_demo_engine


if "ENGINE" not in globals():
    ENGINE = create_demo_engine()

if "LAST_TICK_RESULT" not in globals():
    LAST_TICK_RESULT: dict[str, Any] | None = None


def get_state() -> dict[str, Any]:
    return {
        "state": ENGINE.snapshot(),
        "last_tick_result": LAST_TICK_RESULT,
        "snapshot": build_snapshot(),
    }


def reset_state() -> dict[str, Any]:
    global ENGINE, LAST_TICK_RESULT
    ENGINE = create_demo_engine()
    LAST_TICK_RESULT = None
    return {
        "status": "reset",
        **get_state(),
    }


def tick_world() -> dict[str, Any]:
    global LAST_TICK_RESULT
    result = ENGINE.tick()
    LAST_TICK_RESULT = result.model_dump()
    return {
        "status": "ticked",
        "snapshot": build_snapshot(),
        **LAST_TICK_RESULT,
    }


def process_message(text: str) -> dict[str, Any]:
    global LAST_TICK_RESULT
    enqueue_info = ENGINE.submit_player_action(text)
    result = ENGINE.tick()
    LAST_TICK_RESULT = result.model_dump()
    return {
        "submission": enqueue_info,
        "snapshot": build_snapshot(),
        **LAST_TICK_RESULT,
    }


def build_snapshot() -> dict[str, Any]:
    snapshot = ENGINE.snapshot()
    return {
        "tick": snapshot["tick"],
        "time": f"T+{snapshot['tick'] * ENGINE.state.world.dt_seconds}s",
        "character": {
            "id": ENGINE.state.character.id,
            "name": ENGINE.state.character.name,
            "mood": ENGINE.state.character.mood,
            "stress": ENGINE.state.character.stress,
            "trust": ENGINE.state.character.trust,
            "focus": ENGINE.state.character.focus,
            "fatigue": ENGINE.state.character.fatigue,
            "current_goal": ENGINE.state.character.current_goal,
            "memory_summary": ENGINE.state.character.memory_summary,
        },
        "mental_queue": snapshot["queue"],
        "last_player_action": ENGINE.state.world.last_player_action,
        "scene": {
            "title": "Neural Exchange Watch",
            "location": ENGINE.state.world.location,
        },
        "frame_prompt": (
            f"{ENGINE.state.character.name} in {ENGINE.state.world.location}, "
            f"mood {ENGINE.state.character.mood}, stress {ENGINE.state.character.stress}, "
            f"focus {ENGINE.state.character.focus}, current goal {ENGINE.state.character.current_goal}"
        ),
        "last_event": ENGINE.state.event_log[-1]["type"] if ENGINE.state.event_log else "runtime_initialized",
        "external_action": snapshot["last_external_action"],
    }
