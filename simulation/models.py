from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


MentalProcessType = Literal[
    "perception",
    "interpretation",
    "emotional_response",
    "response_planning",
    "decision",
    "speech_generation",
]
MentalProcessStatus = Literal["pending", "processing", "completed"]


class MentalProcess(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: MentalProcessType
    content: str
    total_cost_ticks: int = Field(ge=1)
    remaining_ticks: int = Field(ge=0)
    status: MentalProcessStatus = "pending"
    result: str | None = None


class CharacterState(BaseModel):
    id: str
    name: str
    mood: str
    stress: int = Field(ge=0, le=100)
    trust: int = Field(ge=0, le=100)
    focus: int = Field(ge=0, le=100)
    fatigue: int = Field(ge=0, le=100)
    current_goal: str
    fears: list[str] = Field(default_factory=list)
    boundaries: list[str] = Field(default_factory=list)
    memory_summary: str
    mental_queue: list[MentalProcess] = Field(default_factory=list)


class WorldState(BaseModel):
    tick: int = 0
    dt_seconds: int = 1
    location: str
    visible_events: list[str] = Field(default_factory=list)
    last_player_action: str | None = None
    canonical_state: dict[str, Any] = Field(default_factory=dict)


class ExternalAction(BaseModel):
    type: Literal["pause", "speech", "action"]
    content: str


class TickDelta(BaseModel):
    character: dict[str, Any] = Field(default_factory=dict)
    world: dict[str, Any] = Field(default_factory=dict)
    queue_updates: list[str] = Field(default_factory=list)


class TickResult(BaseModel):
    tick: int
    objective_facts: dict[str, Any]
    character_perception: list[str] = Field(default_factory=list)
    character_interpretation: list[str] = Field(default_factory=list)
    inner_thoughts: list[str] = Field(default_factory=list)
    completed_processes: list[str] = Field(default_factory=list)
    external_action: ExternalAction
    can_act_externally: bool
    state_delta: TickDelta
    state: CharacterState
    world: WorldState


class SimulationState(BaseModel):
    character: CharacterState
    world: WorldState
    event_log: list[dict[str, Any]] = Field(default_factory=list)
    completed_actions: list[ExternalAction] = Field(default_factory=list)
    pending_external_action: ExternalAction | None = None
    last_external_action: ExternalAction = Field(
        default_factory=lambda: ExternalAction(
            type="pause",
            content="No external action yet. Internal processing continues.",
        )
    )
