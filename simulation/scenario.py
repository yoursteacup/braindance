from __future__ import annotations

from simulation.engine import TickEngine, create_demo_engine
from simulation.models import TickResult


def run_example_scenario() -> list[TickResult]:
    engine: TickEngine = create_demo_engine()
    engine.submit_player_action(
        "Мы всегда в ответе за то, что создаем, поэтому объясни свою позицию спокойно и точно."
    )

    results: list[TickResult] = []
    while True:
        result = engine.tick()
        results.append(result)
        if result.can_act_externally:
            return results
