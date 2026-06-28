from __future__ import annotations

from typing import Any

import local_provider
from simulation.engine import TickEngine, create_demo_engine


if "ENGINE" not in globals():
    ENGINE = create_demo_engine()

if "LAST_TICK_RESULT" not in globals():
    LAST_TICK_RESULT: dict[str, Any] | None = None

if "LAST_DREAM_RESULT" not in globals():
    LAST_DREAM_RESULT: dict[str, Any] | None = None


def get_state() -> dict[str, Any]:
    return {
        "state": ENGINE.snapshot(),
        "last_tick_result": LAST_TICK_RESULT,
        "last_dream_result": LAST_DREAM_RESULT,
        "snapshot": build_snapshot(),
    }


def reset_state() -> dict[str, Any]:
    global ENGINE, LAST_TICK_RESULT, LAST_DREAM_RESULT
    ENGINE = create_demo_engine()
    LAST_TICK_RESULT = None
    LAST_DREAM_RESULT = None
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


def generate_dream() -> dict[str, Any]:
    global LAST_DREAM_RESULT
    snapshot = build_snapshot()
    raw_world = ENGINE.state.world.model_dump()
    user_text = raw_world.get("last_player_action") or snapshot.get("frame_prompt") or ""

    generated_text = local_provider.generate_text(
        snapshot["character"],
        raw_world,
        user_text,
    )
    image_prompt = (
        f"{snapshot.get('frame_prompt', '')}. "
        f"Character speech: {generated_text}. "
        "cinematic still frame, expressive face, coherent environment"
    ).strip()
    image_result = local_provider.generate_image(
        {
            "frame_prompt": image_prompt,
            "snapshot": snapshot,
        }
    )
    LAST_DREAM_RESULT = {
        "status": "ok" if image_result.get("status") == "ok" else "partial",
        "provider_status": local_provider.provider_status(),
        "generated_text": generated_text,
        "image": image_result,
        "source_tick": snapshot["tick"],
        "source_user_text": user_text,
        "frame_prompt": snapshot.get("frame_prompt"),
    }
    return {
        "status": "dream_generated",
        "dream": LAST_DREAM_RESULT,
        "snapshot": build_snapshot(),
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
        "provider_status": local_provider.provider_status(),
        "dream_output": LAST_DREAM_RESULT,
    }
