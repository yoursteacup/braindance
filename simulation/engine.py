from __future__ import annotations

from copy import deepcopy
from typing import Any

from simulation.llm import CharacterLLM, MockCharacterLLM
from simulation.models import (
    CharacterState,
    ExternalAction,
    MentalProcess,
    SimulationState,
    TickDelta,
    TickResult,
    WorldState,
)


class TickEngine:
    def __init__(self, state: SimulationState, llm: CharacterLLM | None = None) -> None:
        self.state = state
        self.llm = llm or MockCharacterLLM()

    def submit_player_action(self, text: str) -> dict[str, Any]:
        self.state.pending_external_action = None
        self.state.last_external_action = ExternalAction(
            type="pause",
            content="No external action yet. Internal processing continues.",
        )
        self.state.world.last_player_action = text
        self.state.world.visible_events.append(f"player_said:{text}")
        self.state.event_log.append(
            {
                "tick": self.state.world.tick,
                "type": "player_action_received",
                "content": text,
            }
        )
        new_processes = self.llm.build_initial_processes(self.state.world, self.state.character, text)
        self.state.character.mental_queue.extend(new_processes)
        return {
            "queued_processes": [process.model_dump() for process in new_processes],
            "queue_size": len(self.state.character.mental_queue),
        }

    def tick(self) -> TickResult:
        self.state.world.tick += 1
        delta = TickDelta()
        perceptions: list[str] = []
        interpretations: list[str] = []
        thoughts: list[str] = []
        completed: list[str] = []
        emitted_action: ExternalAction | None = None

        for process in self._select_processes():
            if not self._can_progress(process):
                delta.queue_updates.append(f"stalled:{process.id}")
                continue

            if process.status == "pending":
                process.status = "processing"

            process.remaining_ticks -= 1
            delta.queue_updates.append(f"progressed:{process.id}:{process.remaining_ticks}")

            if process.remaining_ticks > 0:
                continue

            process.status = "completed"
            directive = self.llm.complete_process(process, self.state)
            process.result = directive.result
            completed.append(process.id)
            self._apply_character_updates(directive.character_updates, delta)
            self._append_spawned_processes(directive.spawned_processes, delta)

            if directive.perception:
                perceptions.append(directive.perception)
            if directive.interpretation:
                interpretations.append(directive.interpretation)
            if directive.inner_thought:
                thoughts.append(directive.inner_thought)
            if directive.external_action:
                emitted_action = directive.external_action
                self.state.pending_external_action = directive.external_action
                self.state.last_external_action = directive.external_action
                self.state.completed_actions.append(directive.external_action)

        self._apply_passive_tick_delta(delta, completed_count=len(completed))
        self._update_memory_summary(perceptions, interpretations, thoughts)

        if self.state.pending_external_action is not None:
            external_action = self.state.pending_external_action
            self.state.pending_external_action = None
        elif self._queue_has_active_work():
            external_action = ExternalAction(
                type="pause",
                content="No external action yet. Internal processing continues.",
            )
        else:
            external_action = self.state.last_external_action

        self.state.event_log.append(
            {
                "tick": self.state.world.tick,
                "type": "tick",
                "completed_processes": completed,
                "external_action": external_action.model_dump(),
                "emitted_action": emitted_action.model_dump() if emitted_action else None,
            }
        )

        return TickResult(
            tick=self.state.world.tick,
            objective_facts={
                "canonical_state": deepcopy(self.state.world.canonical_state),
                "visible_events": list(self.state.world.visible_events),
                "last_player_action": self.state.world.last_player_action,
            },
            character_perception=perceptions,
            character_interpretation=interpretations,
            inner_thoughts=thoughts,
            completed_processes=completed,
            external_action=external_action,
            can_act_externally=external_action.type != "pause",
            state_delta=delta,
            state=self.state.character.model_copy(deep=True),
            world=self.state.world.model_copy(deep=True),
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "tick": self.state.world.tick,
            "character": self.state.character.model_dump(),
            "world": self.state.world.model_dump(),
            "queue": [process.model_dump() for process in self.state.character.mental_queue],
            "event_log_size": len(self.state.event_log),
            "pending_external_action": (
                self.state.pending_external_action.model_dump()
                if self.state.pending_external_action
                else None
            ),
            "last_external_action": self.state.last_external_action.model_dump(),
        }

    def reset(self) -> None:
        fresh = create_demo_engine()
        self.state = fresh.state
        self.llm = fresh.llm

    def _select_processes(self) -> list[MentalProcess]:
        capacity = self._cognitive_capacity()
        active: list[MentalProcess] = []
        for process in self.state.character.mental_queue:
            if process.status == "completed":
                continue
            active.append(process)
            if len(active) >= capacity:
                break
        return active

    def _cognitive_capacity(self) -> int:
        character = self.state.character
        if character.focus >= 70 and character.fatigue <= 40:
            return 2
        return 1

    def _can_progress(self, process: MentalProcess) -> bool:
        if self.state.character.focus >= 40 or process.type == "perception":
            return True
        return self.state.world.tick % 2 == 0

    def _apply_character_updates(self, updates: dict[str, Any], delta: TickDelta) -> None:
        for field, value in updates.items():
            current = getattr(self.state.character, field)
            if isinstance(current, int) and isinstance(value, int):
                if field == "trust":
                    new_value = self._clamp(current + value)
                else:
                    new_value = self._clamp(value)
                setattr(self.state.character, field, new_value)
                delta.character[field] = new_value
                continue

            setattr(self.state.character, field, value)
            delta.character[field] = value

    def _append_spawned_processes(self, processes: list[MentalProcess], delta: TickDelta) -> None:
        self.state.character.mental_queue.extend(processes)
        delta.queue_updates.extend(f"spawned:{process.id}" for process in processes)

    def _apply_passive_tick_delta(self, delta: TickDelta, completed_count: int) -> None:
        queue_active = self._queue_has_active_work()
        if queue_active:
            self.state.character.fatigue = self._clamp(self.state.character.fatigue + 1)
            delta.character["fatigue"] = self.state.character.fatigue

            focus_drop = 1 if self.state.character.focus >= 40 else 0
            if focus_drop:
                self.state.character.focus = self._clamp(self.state.character.focus - focus_drop)
                delta.character["focus"] = self.state.character.focus
        else:
            self.state.character.focus = self._clamp(self.state.character.focus + 1)
            delta.character["focus"] = self.state.character.focus

        if completed_count == 0 and queue_active:
            self.state.character.stress = self._clamp(self.state.character.stress + 1)
            delta.character["stress"] = self.state.character.stress

    def _update_memory_summary(
        self,
        perceptions: list[str],
        interpretations: list[str],
        thoughts: list[str],
    ) -> None:
        latest = perceptions[-1:] + interpretations[-1:] + thoughts[-1:]
        if latest:
            self.state.character.memory_summary = latest[-1]

    def _queue_has_active_work(self) -> bool:
        return any(process.status != "completed" for process in self.state.character.mental_queue)

    @staticmethod
    def _clamp(value: int, minimum: int = 0, maximum: int = 100) -> int:
        return max(minimum, min(maximum, value))


def create_demo_engine() -> TickEngine:
    state = SimulationState(
        character=CharacterState(
            id="mara-01",
            name="Mara",
            mood="calm",
            stress=20,
            trust=50,
            focus=75,
            fatigue=10,
            current_goal="understand the player before responding",
            fears=["loss of agency", "contradicting canonical truth"],
            boundaries=["will not self-harm", "will not invent objective facts"],
            memory_summary="The runtime is quiet.",
        ),
        world=WorldState(
            tick=0,
            dt_seconds=2,
            location="Neural Exchange",
            visible_events=[],
            last_player_action=None,
            canonical_state={
                "time_of_day": "night",
                "weather": "acid rain",
                "threat_level": "moderate",
            },
        ),
    )
    return TickEngine(state=state, llm=MockCharacterLLM())
