# Handoff

Project state as of 2026-06-28.

## Current shape

The app is a live FastAPI runtime with an in-browser dashboard.

Primary files:
- [main.py](/home/ivsed/braindance/main.py:1)
- [live_logic.py](/home/ivsed/braindance/live_logic.py:1)
- [runtime_control.py](/home/ivsed/braindance/runtime_control.py:1)
- [simulation/engine.py](/home/ivsed/braindance/simulation/engine.py:1)
- [simulation/llm.py](/home/ivsed/braindance/simulation/llm.py:1)
- [simulation/models.py](/home/ivsed/braindance/simulation/models.py:1)
- [tests/test_tick_engine.py](/home/ivsed/braindance/tests/test_tick_engine.py:1)

## What already works

- `GET /` returns a built-in HTML dashboard from `main.py`.
- `POST /process`, `POST /runtime/start`, `POST /runtime/stop`, `POST /reset` work through REST.
- `WS /ws` streams runtime snapshots to the browser.
- Runtime cadence is already `1 tick = 2 real seconds`.
- Dashboard includes:
  - character state
  - active mental process
  - collapsible mental queue
  - frame preview
  - shot timeline
  - chat log
  - debug drawer
- Layout is already rebalanced around the frame preview:
  - left: character + active process + mental queue
  - center: frame preview + player input + chat log
  - right: runtime controls + shot timeline + debug

## Important implementation notes

- `main.py` contains the server and the full inline dashboard HTML/CSS/JS.
- `live_logic.py` is a thin adapter over the simulation engine and builds the snapshot sent to the UI.
- `runtime_control.py` runs the background loop and broadcasts snapshots over websocket.
- `simulation/engine.py` contains the tick engine and current runtime behavior.

## Current architectural problem

The next session should not focus on more UI polish first. The main issue is the runtime data model.

### 1. `external_action` is behaving like state, not like an event

Current behavior:
- after `speech_generation` completes, the same speech keeps appearing across later ticks
- this was introduced as a persistence fix, but semantically it is wrong

Desired behavior:
- `speech_emitted` should exist for one tick/event only
- next tick should return to `idle` unless something new happens

Relevant code:
- [simulation/engine.py](/home/ivsed/braindance/simulation/engine.py:19)

### 2. `mental_queue` still contains completed processes

Right now it acts as both:
- active queue
- historical log

Desired behavior:
- `mental_queue` should contain only active/pending/processing work
- completed processes should move to a separate history/log structure

### 3. `frame_prompt` is still too flat

The runtime already exposes some scene data in `live_logic.py`, but the proper next step is a structured frame object:
- `scene`
- `camera`
- `character`
- `action`

### 4. `chat log` is derived from snapshots instead of proper events

The UI currently deduplicates repeated speech on the frontend.
That is a workaround, not the right architecture.

## Recommended next step

Refactor the runtime from snapshot-first toward event-driven behavior.

### Target direction

Keep:
- initial snapshot for connect/reconnect

Add:
- runtime event bus semantics
- one-shot runtime events
- active-only mental queue
- completed process history
- structured frame state

### Suggested event types

- `speech_emitted`
- `thought_started`
- `thought_completed`
- `emotion_changed`
- `goal_changed`
- `camera_changed`
- `world_changed`

## Concrete next refactor

1. Add runtime event models in [simulation/models.py](/home/ivsed/braindance/simulation/models.py:1)
2. Change [simulation/engine.py](/home/ivsed/braindance/simulation/engine.py:1) so `tick()` produces:
   - current snapshot/state
   - emitted events for this tick
3. Make speech one-shot:
   - emit `speech_emitted` on the completion tick
   - do not persist the same speech as the default external action forever
4. Remove completed items from `mental_queue`
5. Introduce separate completed process history
6. Replace flat frame prompt logic with structured frame state
7. Update websocket payload semantics in [live_logic.py](/home/ivsed/braindance/live_logic.py:1)
8. Update dashboard in [main.py](/home/ivsed/braindance/main.py:1) to consume events instead of inferring behavior from repeated snapshots

## What not to do next

- Do not spend the next session on more cosmetic UI tuning first
- Do not add SSE yet
- Do not keep expanding the flat snapshot shape as a substitute for events
- Do not fix repeated speech only in frontend code

## Good starting task for next session

"Refactor runtime from snapshot-first to event-driven. Keep initial snapshot for reconnect, add runtime event semantics over the existing websocket, make speech one-shot, keep `mental_queue` active-only, and move completed processes into history."
