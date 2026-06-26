from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from simulation.models import CharacterState, ExternalAction, MentalProcess, SimulationState, WorldState


@dataclass
class CompletionDirective:
    result: str
    perception: str | None = None
    interpretation: str | None = None
    inner_thought: str | None = None
    character_updates: dict[str, int | str] = field(default_factory=dict)
    spawned_processes: list[MentalProcess] = field(default_factory=list)
    external_action: ExternalAction | None = None


class CharacterLLM(Protocol):
    def build_initial_processes(self, world: WorldState, character: CharacterState, text: str) -> list[MentalProcess]:
        ...

    def complete_process(
        self,
        process: MentalProcess,
        state: SimulationState,
    ) -> CompletionDirective:
        ...


class MockCharacterLLM:
    def build_initial_processes(
        self,
        world: WorldState,
        character: CharacterState,
        text: str,
    ) -> list[MentalProcess]:
        return [
            MentalProcess(
                type="perception",
                content=text,
                total_cost_ticks=1,
                remaining_ticks=1,
            )
        ]

    def complete_process(
        self,
        process: MentalProcess,
        state: SimulationState,
    ) -> CompletionDirective:
        text = process.content
        stress = state.character.stress

        if process.type == "perception":
            interpretation_cost = 2 + self._complexity_penalty(text) + self._stress_penalty(stress)
            return CompletionDirective(
                result=f"Heard the player say: {text}",
                perception=f"{state.character.name} notices the player's words: {text}",
                spawned_processes=[
                    MentalProcess(
                        type="interpretation",
                        content=text,
                        total_cost_ticks=interpretation_cost,
                        remaining_ticks=interpretation_cost,
                    )
                ],
            )

        if process.type == "interpretation":
            return CompletionDirective(
                result=f"Interpreted intent behind: {text}",
                interpretation=self._interpretation_text(text),
                spawned_processes=[
                    MentalProcess(
                        type="emotional_response",
                        content=text,
                        total_cost_ticks=1,
                        remaining_ticks=1,
                    )
                ],
            )

        if process.type == "emotional_response":
            updates = self._emotion_updates(text, stress)
            planning_cost = 2 + self._stress_penalty(stress)
            return CompletionDirective(
                result=f"Emotional response formed around: {text}",
                inner_thought=self._emotion_text(text, stress),
                character_updates=updates,
                spawned_processes=[
                    MentalProcess(
                        type="response_planning",
                        content=text,
                        total_cost_ticks=planning_cost,
                        remaining_ticks=planning_cost,
                    )
                ],
            )

        if process.type == "response_planning":
            return CompletionDirective(
                result=f"Response strategy formed for: {text}",
                inner_thought=self._planning_text(text, stress),
                character_updates={"current_goal": "answer the player clearly"},
                spawned_processes=[
                    MentalProcess(
                        type="decision",
                        content=text,
                        total_cost_ticks=1,
                        remaining_ticks=1,
                    )
                ],
            )

        if process.type == "decision":
            speech_cost = 1 + self._stress_penalty(stress)
            return CompletionDirective(
                result="Decision to speak is ready.",
                inner_thought="The character commits to an outward response.",
                spawned_processes=[
                    MentalProcess(
                        type="speech_generation",
                        content=text,
                        total_cost_ticks=speech_cost,
                        remaining_ticks=speech_cost,
                    )
                ],
            )

        if process.type == "speech_generation":
            return CompletionDirective(
                result="Speech is fully formed.",
                external_action=ExternalAction(
                    type="speech",
                    content=self._speech_text(text, state.character),
                ),
            )

        raise ValueError(f"Unsupported process type: {process.type}")

    def _complexity_penalty(self, text: str) -> int:
        word_count = len(text.split())
        return 1 if word_count >= 8 else 0

    def _stress_penalty(self, stress: int) -> int:
        return 1 if stress >= 70 else 0

    def _interpretation_text(self, text: str) -> str:
        if "ответ" in text.lower() or "responsib" in text.lower():
            return "The character interprets the message as a moral demand."
        return "The character works through the likely intent behind the message."

    def _emotion_updates(self, text: str, stress: int) -> dict[str, int | str]:
        if "угроза" in text.lower() or "threat" in text.lower():
            return {"stress": min(100, stress + 10), "mood": "guarded"}
        if stress >= 70:
            return {"stress": min(100, stress + 2), "mood": "impulsive"}
        return {"trust": 1, "mood": "reflective"}

    def _emotion_text(self, text: str, stress: int) -> str:
        if stress >= 70:
            return "Stress spikes and compresses the emotional reaction into something sharp."
        return f"The character lets the meaning of '{text}' settle emotionally."

    def _planning_text(self, text: str, stress: int) -> str:
        if stress >= 70:
            return "Planning is fragmented; the response is likely to be abrupt."
        return f"The character weighs how to answer '{text}' without crossing boundaries."

    def _speech_text(self, text: str, character: CharacterState) -> str:
        if character.stress >= 70 or character.mood == "impulsive":
            return f"{character.name} answers abruptly: '{text}... Fine. Here's my position.'"
        return f"{character.name} answers after thinking: 'I heard you. Here is my considered response.'"
