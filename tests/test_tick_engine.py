from __future__ import annotations

from simulation.engine import TickEngine, create_demo_engine
from simulation.models import MentalProcess


def tick_until_response(engine: TickEngine, limit: int = 20) -> int:
    for step in range(1, limit + 1):
        result = engine.tick()
        if result.can_act_externally:
            return step
    raise AssertionError("response was not produced in time")


def test_process_with_cost_three_cannot_complete_early() -> None:
    engine = create_demo_engine()
    engine.state.character.mental_queue = [
        MentalProcess(
            type="interpretation",
            content="complex thought",
            total_cost_ticks=3,
            remaining_ticks=3,
        )
    ]

    first = engine.tick()
    second = engine.tick()
    third = engine.tick()

    assert first.completed_processes == []
    assert second.completed_processes == []
    assert len(third.completed_processes) == 1


def test_speech_generation_blocks_full_dialogue_until_completed() -> None:
    engine = create_demo_engine()
    engine.submit_player_action("Explain what this world means to you in detail.")

    final = None
    for _ in range(20):
        result = engine.tick()
        if result.can_act_externally:
            final = result
            break

        assert result.external_action.type == "pause"
        assert result.can_act_externally is False

    assert final is not None
    assert final.external_action.type == "speech"
    assert final.can_act_externally is True


def test_last_external_action_persists_after_queue_completion() -> None:
    engine = create_demo_engine()
    engine.submit_player_action("Tell me what you intend to do next.")

    final = None
    for _ in range(20):
        result = engine.tick()
        if result.can_act_externally:
            final = result
            break

    assert final is not None
    assert engine.state.last_external_action.type == "speech"

    next_tick = engine.tick()
    assert next_tick.external_action.type == "speech"
    assert next_tick.external_action.content == engine.state.last_external_action.content


def test_new_process_clears_previous_external_action() -> None:
    engine = create_demo_engine()
    engine.submit_player_action("Tell me what you intend to do next.")
    for _ in range(20):
        if engine.tick().can_act_externally:
            break

    assert engine.state.last_external_action.type == "speech"

    engine.submit_player_action("A new question needs a new answer.")
    assert engine.state.last_external_action.type == "pause"
    assert engine.state.pending_external_action is None

    result = engine.tick()
    assert result.external_action.type == "pause"


def test_high_stress_requires_more_ticks_for_response() -> None:
    calm_engine = create_demo_engine()
    calm_engine.submit_player_action("Tell me what you intend to do next.")

    stressed_engine = create_demo_engine()
    stressed_engine.state.character.stress = 85
    stressed_engine.submit_player_action("Tell me what you intend to do next.")

    calm_ticks = tick_until_response(calm_engine)
    stressed_ticks = tick_until_response(stressed_engine)

    assert stressed_ticks > calm_ticks


def test_low_focus_slows_queue_processing() -> None:
    focused_engine = create_demo_engine()
    focused_engine.submit_player_action("Interpret this difficult statement carefully.")

    low_focus_engine = create_demo_engine()
    low_focus_engine.state.character.focus = 20
    low_focus_engine.submit_player_action("Interpret this difficult statement carefully.")

    focused_ticks = tick_until_response(focused_engine)
    low_focus_ticks = tick_until_response(low_focus_engine)

    assert low_focus_ticks > focused_ticks


def test_state_delta_applies_after_each_tick() -> None:
    engine = create_demo_engine()
    engine.submit_player_action("Simple message.")

    result = engine.tick()

    assert "fatigue" in result.state_delta.character
    assert result.state_delta.character["fatigue"] == engine.state.character.fatigue
    assert engine.state.character.fatigue > 10
