from __future__ import annotations

import importlib

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

import runtime_control


app = FastAPI(title="Braindance Runtime")


class ProcessRequest(BaseModel):
    text: str


def logic():
    import live_logic

    return importlib.reload(live_logic)


@app.on_event("startup")
async def startup() -> None:
    await runtime_control.start_runtime()


@app.on_event("shutdown")
async def shutdown() -> None:
    await runtime_control.stop_runtime()


@app.get("/")
def root() -> HTMLResponse:
    return HTMLResponse(
        """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Braindance Runtime Dashboard</title>
  <style>
    :root {
      --bg: #08111a;
      --panel: #101d29;
      --panel-alt: #0d1721;
      --line: #22384b;
      --text: #d8e6f3;
      --muted: #7f97ab;
      --accent: #6ee7ff;
      --accent-strong: #ff8a5b;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "IBM Plex Mono", "Fira Code", monospace;
      color: var(--text);
      background:
        radial-gradient(circle at top, rgba(110, 231, 255, 0.14), transparent 28%),
        linear-gradient(180deg, #050a0f, var(--bg));
    }
    .wrap {
      width: min(1400px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 16px 0 24px;
    }
    .hero {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      margin-bottom: 12px;
    }
    .panel {
      background: linear-gradient(180deg, rgba(16, 29, 41, 0.96), rgba(13, 23, 33, 0.96));
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 14px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
    }
    .title {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      color: var(--muted);
      margin-bottom: 10px;
    }
    .metric {
      font-size: clamp(28px, 6vw, 54px);
      line-height: 1;
      color: var(--accent);
    }
    .sub {
      margin-top: 6px;
      color: var(--muted);
      font-size: 13px;
    }
    .grid {
      display: grid;
      gap: 12px;
      grid-template-columns: 320px minmax(520px, 1fr) 360px;
      align-items: start;
    }
    .hero .panel.connection-panel {
      display: grid;
      gap: 10px;
      align-content: start;
    }
    .stack {
      display: grid;
      gap: 12px;
    }
    .kv {
      display: grid;
      gap: 10px;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    }
    .kv div {
      padding: 10px 12px;
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.04);
    }
    .kv strong, .action-type {
      display: block;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--muted);
      margin-bottom: 4px;
    }
    .queue {
      display: grid;
      gap: 10px;
      max-height: 320px;
      overflow: auto;
    }
    details {
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid rgba(255, 255, 255, 0.04);
      padding: 10px 12px 12px;
    }
    summary {
      cursor: pointer;
      list-style: none;
      color: var(--text);
      font-size: 13px;
    }
    summary::-webkit-details-marker {
      display: none;
    }
    summary::before {
      content: "+";
      display: inline-block;
      width: 14px;
      margin-right: 8px;
      color: var(--accent);
    }
    details[open] summary::before {
      content: "-";
    }
    .details-body {
      margin-top: 12px;
    }
    .queue-item {
      padding: 12px;
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(110, 231, 255, 0.12);
    }
    .queue-item.active {
      border-color: var(--accent-strong);
      box-shadow: inset 0 0 0 1px rgba(255, 138, 91, 0.25);
    }
    .queue-item header {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 8px;
      color: var(--accent);
      font-size: 13px;
    }
    .queue-item p {
      margin: 0 0 8px;
      color: var(--text);
      word-break: break-word;
    }
    .queue-meta {
      color: var(--muted);
      font-size: 12px;
    }
    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      color: var(--text);
      font-size: 13px;
      line-height: 1.45;
    }
    .chat {
      margin-top: 8px;
      display: grid;
      gap: 12px;
    }
    .chat-row {
      display: grid;
      gap: 12px;
      grid-template-columns: 1fr auto;
    }
    input, button {
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px 16px;
      font: inherit;
    }
    input {
      color: var(--text);
      background: rgba(255, 255, 255, 0.04);
    }
    button {
      background: linear-gradient(135deg, var(--accent), var(--accent-strong));
      color: #041019;
      font-weight: 700;
      cursor: pointer;
    }
    .status {
      color: var(--muted);
      font-size: 13px;
      min-height: 18px;
    }
    .toolbar {
      display: grid;
      gap: 8px;
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
    .toolbar button {
      padding: 10px 12px;
      font-size: 12px;
    }
    .log {
      display: grid;
      gap: 10px;
      max-height: 240px;
      overflow: auto;
    }
    .log-item {
      padding: 10px 12px;
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .log-item strong {
      display: block;
      margin-bottom: 4px;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--muted);
    }
    .timeline {
      display: grid;
      gap: 10px;
      grid-auto-flow: column;
      grid-auto-columns: 140px;
      overflow-x: auto;
      padding-bottom: 4px;
    }
    .shot-card {
      padding: 10px;
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.06);
      min-height: 92px;
    }
    .shot-card.current {
      border-color: var(--accent-strong);
      box-shadow: inset 0 0 0 1px rgba(255, 138, 91, 0.24);
    }
    .shot-tick {
      color: var(--accent);
      font-size: 12px;
      margin-bottom: 8px;
    }
    .shot-mood {
      font-size: 13px;
      margin-bottom: 8px;
      color: var(--text);
    }
    .shot-meta {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }
    .badge {
      display: inline-block;
      padding: 5px 8px;
      border-radius: 999px;
      border: 1px solid var(--line);
      color: var(--text);
      font-size: 12px;
      background: rgba(255, 255, 255, 0.03);
    }
    .frame-preview {
      position: relative;
      overflow: hidden;
      min-height: 340px;
      background:
        radial-gradient(circle at 20% 20%, rgba(110, 231, 255, 0.2), transparent 30%),
        radial-gradient(circle at 80% 30%, rgba(255, 138, 91, 0.18), transparent 28%),
        linear-gradient(180deg, rgba(8, 17, 26, 0.92), rgba(4, 9, 15, 0.98));
    }
    .frame-preview::after {
      content: "";
      position: absolute;
      inset: 0;
      background: linear-gradient(180deg, transparent 0%, rgba(3, 8, 14, 0.7) 100%);
      pointer-events: none;
    }
    .frame-preview > * {
      position: relative;
      z-index: 1;
    }
    .frame-kicker {
      color: var(--accent);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.18em;
      margin-bottom: 8px;
    }
    .frame-heading {
      font-size: clamp(24px, 4vw, 36px);
      line-height: 1.05;
      margin: 0 0 8px;
    }
    .frame-subtitle {
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 16px;
    }
    .frame-description {
      font-size: 14px;
      line-height: 1.5;
      margin-bottom: 18px;
      max-width: 56ch;
    }
    .indicator-row {
      display: grid;
      gap: 10px;
      grid-template-columns: 1fr 1fr;
      margin-bottom: 14px;
    }
    .indicator-label {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }
    .indicator-bar {
      height: 10px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.06);
      overflow: hidden;
    }
    .indicator-fill {
      height: 100%;
      border-radius: 999px;
      transition: width 180ms ease, background-color 180ms ease;
    }
    .frame-mood {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 10px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.08);
      font-size: 12px;
      color: var(--text);
    }
    .chat-panel {
      min-height: 0;
    }
    @media (max-width: 1200px) {
      .grid {
        grid-template-columns: 300px minmax(420px, 1fr) 320px;
      }
    }
    @media (max-width: 980px) {
      .grid {
        grid-template-columns: 1fr;
      }
      .chat-row {
        grid-template-columns: 1fr;
      }
      .toolbar {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="panel">
        <div class="title">Runtime Tick</div>
        <div class="metric" id="tick">-</div>
        <div class="sub" id="simTime">Waiting for stream</div>
      </div>
      <div class="panel">
        <div class="title">External Action</div>
        <div class="action-type" id="actionType">pause</div>
        <pre id="actionContent">No external action yet.</pre>
      </div>
      <div class="panel connection-panel">
        <div class="title">Connection</div>
        <div class="metric" id="connection">disconnected</div>
        <div class="sub" id="connectionText">Connecting...</div>
        <div class="badge" id="receivedAt">No packets yet</div>
      </div>
    </section>

    <section class="grid">
      <div class="stack">
        <div class="panel">
          <div class="title">Character State</div>
          <div class="kv" id="characterState"></div>
        </div>
        <div class="panel">
          <div class="title">Active Process</div>
          <pre id="activeProcess">idle</pre>
        </div>
        <div class="panel">
          <div class="title">Mental Queue</div>
          <details id="queueDetails">
            <summary id="queueSummary">Queue</summary>
            <div class="details-body">
              <div class="queue" id="mentalQueue"></div>
            </div>
          </details>
        </div>
      </div>

      <div class="stack">
        <div class="panel">
          <div class="title">Frame Preview</div>
          <div class="frame-preview" id="framePreview">
            <div class="frame-kicker" id="frameKicker">Scene Booting</div>
            <h2 class="frame-heading" id="frameHeading">Waiting for runtime</h2>
            <div class="frame-subtitle" id="frameSubtitle">No external action yet.</div>
            <div class="frame-description" id="frameDescription">The cinematic placeholder will update from the runtime stream.</div>
            <div class="indicator-row">
              <div>
                <div class="indicator-label"><span>Stress</span><span id="stressValue">0</span></div>
                <div class="indicator-bar"><div class="indicator-fill" id="stressBar"></div></div>
              </div>
              <div>
                <div class="indicator-label"><span>Focus</span><span id="focusValue">0</span></div>
                <div class="indicator-bar"><div class="indicator-fill" id="focusBar"></div></div>
              </div>
            </div>
            <div class="frame-mood" id="frameMood">Mood unknown</div>
            <div class="details-body" style="margin-top: 18px;">
              <pre id="framePrompt"></pre>
            </div>
          </div>
        </div>
        <div class="panel">
          <div class="title">Player Input</div>
          <form class="chat" id="chatForm">
            <div class="chat-row">
              <input id="chatInput" name="text" type="text" placeholder="Send a message into the runtime..." autocomplete="off" required>
              <button type="submit" id="sendButton">Send</button>
            </div>
            <div class="status" id="chatStatus"></div>
          </form>
        </div>
        <div class="panel chat-panel">
          <div class="title">Chat Log</div>
          <div class="log" id="chatLog"></div>
        </div>
      </div>

      <div class="stack">
        <div class="panel">
          <div class="title">Runtime Controls</div>
          <div class="toolbar">
            <button type="button" id="startRuntime">Start Runtime</button>
            <button type="button" id="stopRuntime">Stop Runtime</button>
            <button type="button" id="resetState">Reset State</button>
          </div>
          <div class="status" id="runtimeStatus"></div>
        </div>
        <div class="panel">
          <div class="title">Shot Timeline</div>
          <div class="timeline" id="shotTimeline"></div>
        </div>
        <div class="panel">
          <div class="title">Debug</div>
          <details>
            <summary>Debug JSON</summary>
            <div class="details-body">
              <pre id="rawSnapshot"></pre>
            </div>
          </details>
        </div>
      </div>
    </section>
  </div>

  <script>
    const tickNode = document.getElementById("tick");
    const simTimeNode = document.getElementById("simTime");
    const actionTypeNode = document.getElementById("actionType");
    const actionContentNode = document.getElementById("actionContent");
    const connectionNode = document.getElementById("connection");
    const connectionTextNode = document.getElementById("connectionText");
    const receivedAtNode = document.getElementById("receivedAt");
    const characterStateNode = document.getElementById("characterState");
    const activeProcessNode = document.getElementById("activeProcess");
    const queueSummaryNode = document.getElementById("queueSummary");
    const mentalQueueNode = document.getElementById("mentalQueue");
    const frameKickerNode = document.getElementById("frameKicker");
    const frameHeadingNode = document.getElementById("frameHeading");
    const frameSubtitleNode = document.getElementById("frameSubtitle");
    const frameDescriptionNode = document.getElementById("frameDescription");
    const frameMoodNode = document.getElementById("frameMood");
    const stressValueNode = document.getElementById("stressValue");
    const focusValueNode = document.getElementById("focusValue");
    const stressBarNode = document.getElementById("stressBar");
    const focusBarNode = document.getElementById("focusBar");
    const framePromptNode = document.getElementById("framePrompt");
    const shotTimelineNode = document.getElementById("shotTimeline");
    const chatLogNode = document.getElementById("chatLog");
    const chatForm = document.getElementById("chatForm");
    const chatInput = document.getElementById("chatInput");
    const chatStatus = document.getElementById("chatStatus");
    const sendButton = document.getElementById("sendButton");
    const startRuntimeButton = document.getElementById("startRuntime");
    const stopRuntimeButton = document.getElementById("stopRuntime");
    const resetStateButton = document.getElementById("resetState");
    const runtimeStatusNode = document.getElementById("runtimeStatus");

    const chatLog = [];
    const shotHistory = [];
    let lastSpeechSignature = null;

    function renderCharacter(character) {
      const entries = Object.entries(character || {});
      characterStateNode.innerHTML = entries.map(([key, value]) => {
        return `<div><strong>${key}</strong><span>${String(value)}</span></div>`;
      }).join("");
    }

    function renderActiveProcess(queue, externalAction) {
      const active = (queue || []).find((item) => item.status !== "completed");
      if (active) {
        activeProcessNode.textContent =
          `${active.type} | ${active.status} | remaining ${active.remaining_ticks}/${active.total_cost_ticks}`;
        return;
      }

      if (externalAction?.type === "speech") {
        activeProcessNode.textContent = "speech ready";
        return;
      }

      activeProcessNode.textContent = "idle";
    }

    function renderQueue(queue) {
      const activeCount = (queue || []).filter((item) => item.status !== "completed").length;
      queueSummaryNode.textContent = `Queue ${queue?.length ?? 0} items | active ${activeCount}`;

      if (!queue || queue.length === 0) {
        mentalQueueNode.innerHTML = '<div class="queue-item"><p>Mental queue is empty.</p></div>';
        return;
      }

      const activeId = queue.find((item) => item.status !== "completed")?.id;
      mentalQueueNode.innerHTML = queue.map((item) => {
        return `
          <article class="queue-item ${item.id === activeId ? "active" : ""}">
            <header>
              <span>${item.type}</span>
              <span>${item.status}</span>
            </header>
            <p>${item.content}</p>
            <div class="queue-meta">ticks ${item.total_cost_ticks} | remaining ${item.remaining_ticks}</div>
            <div class="queue-meta">${item.result || "result pending"}</div>
          </article>
        `;
      }).join("");
    }

    function moodColor(mood, stress, focus) {
      if (stress >= 70) return "#ff8a5b";
      if (focus >= 75) return "#6ee7ff";
      if ((mood || "").includes("reflect")) return "#8df0c8";
      return "#9db7cb";
    }

    function buildCinematicDescription(snapshot) {
      const location = snapshot.scene?.location || "Unknown location";
      const mood = snapshot.character?.mood || "unknown";
      const stress = snapshot.character?.stress ?? 0;
      const focus = snapshot.character?.focus ?? 0;
      return `${snapshot.character?.name || "Character"} holds the frame in ${location}. ` +
        `The scene carries a ${mood} tone, stress at ${stress}, focus at ${focus}, ` +
        `while the runtime projects: ${snapshot.frame_prompt || "no prompt available"}`;
    }

    function renderFramePreview(snapshot) {
      const sceneTitle = snapshot.scene?.title || "Runtime Scene";
      const location = snapshot.scene?.location || "Unknown location";
      const mood = snapshot.character?.mood || "unknown";
      const stress = snapshot.character?.stress ?? 0;
      const focus = snapshot.character?.focus ?? 0;
      const action = snapshot.external_action?.content || "No external action yet.";
      const accent = moodColor(mood, stress, focus);

      frameKickerNode.textContent = location;
      frameHeadingNode.textContent = sceneTitle;
      frameSubtitleNode.textContent = action;
      frameDescriptionNode.textContent = buildCinematicDescription(snapshot);
      frameMoodNode.textContent = `Mood: ${mood}`;
      frameMoodNode.style.borderColor = accent;
      frameMoodNode.style.color = accent;
      stressValueNode.textContent = String(stress);
      focusValueNode.textContent = String(focus);
      stressBarNode.style.width = `${Math.max(0, Math.min(100, stress))}%`;
      focusBarNode.style.width = `${Math.max(0, Math.min(100, focus))}%`;
      stressBarNode.style.backgroundColor = stress >= 70 ? "#ff8a5b" : "#ffb36b";
      focusBarNode.style.backgroundColor = focus >= 70 ? "#6ee7ff" : "#8df0c8";
      frameHeadingNode.style.color = accent;
    }

    function updateShotHistory(snapshot) {
      const last = shotHistory[shotHistory.length - 1];
      if (last && last.tick === snapshot.tick) {
        shotHistory[shotHistory.length - 1] = snapshot;
      } else {
        shotHistory.push(snapshot);
      }

      while (shotHistory.length > 6) {
        shotHistory.shift();
      }
    }

    function renderShotTimeline() {
      if (shotHistory.length === 0) {
        shotTimelineNode.innerHTML = '<div class="shot-card"><div class="shot-meta">No frames received yet.</div></div>';
        return;
      }

      const currentTick = shotHistory[shotHistory.length - 1].tick;
      shotTimelineNode.innerHTML = shotHistory.slice().reverse().map((shot) => `
        <article class="shot-card ${shot.tick === currentTick ? "current" : ""}">
          <div class="shot-tick">tick ${shot.tick}</div>
          <div class="shot-mood">${shot.character?.mood || "unknown mood"}</div>
          <div class="shot-meta">stress ${shot.character?.stress ?? 0} · focus ${shot.character?.focus ?? 0}</div>
          <div class="shot-meta">${shot.external_action?.type || "pause"}</div>
        </article>
      `).join("");
    }

    function addLogEntry(role, content) {
      chatLog.unshift({
        role,
        content,
        timestamp: new Date().toLocaleTimeString(),
      });

      if (chatLog.length > 24) {
        chatLog.length = 24;
      }

      chatLogNode.innerHTML = chatLog.map((entry) => `
        <article class="log-item">
          <strong>${entry.role} · ${entry.timestamp}</strong>
          <div>${entry.content}</div>
        </article>
      `).join("");
    }

    function renderSnapshot(snapshot) {
      tickNode.textContent = snapshot.tick ?? "-";
      simTimeNode.textContent = snapshot.time ?? "";
      actionTypeNode.textContent = snapshot.external_action?.type ?? "pause";
      actionContentNode.textContent = snapshot.external_action?.content ?? "No external action yet.";
      receivedAtNode.textContent = `received ${new Date().toLocaleTimeString()}`;
      framePromptNode.textContent = snapshot.frame_prompt ?? "";
      renderCharacter(snapshot.character);
      renderActiveProcess(snapshot.mental_queue, snapshot.external_action);
      renderQueue(snapshot.mental_queue);
      renderFramePreview(snapshot);
      updateShotHistory(snapshot);
      renderShotTimeline();

      const speech = snapshot.external_action;
      const speechSignature = speech?.type === "speech" ? `${snapshot.tick}:${speech.content}` : null;
      if (speechSignature && speechSignature !== lastSpeechSignature) {
        addLogEntry("runtime", speech.content);
        lastSpeechSignature = speechSignature;
      }
    }

    function setConnection(online, text) {
      connectionNode.textContent = online ? "connected" : "disconnected";
      connectionTextNode.textContent = text;
    }

    async function callEndpoint(path, method = "POST") {
      const response = await fetch(path, { method });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response.json();
    }

    function connect() {
      const protocol = window.location.protocol === "https:" ? "wss" : "ws";
      const socket = new WebSocket(`${protocol}://${window.location.host}/ws`);

      socket.addEventListener("open", () => {
        setConnection(true, "connected");
      });

      socket.addEventListener("message", (event) => {
        renderSnapshot(JSON.parse(event.data));
      });

      socket.addEventListener("close", () => {
        setConnection(false, "disconnected");
        window.setTimeout(connect, 1000);
      });

      socket.addEventListener("error", () => {
        setConnection(false, "socket error");
        socket.close();
      });
    }

    chatForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const text = chatInput.value.trim();
      if (!text) {
        return;
      }

      sendButton.disabled = true;
      chatStatus.textContent = "Sending message into runtime...";

      try {
        addLogEntry("user", text);
        lastSpeechSignature = null;
        const response = await fetch("/process", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text }),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const payload = await response.json();
        renderSnapshot(payload.snapshot);
        chatInput.value = "";
        chatStatus.textContent = "Message accepted. Waiting for further ticks.";
      } catch (error) {
        chatStatus.textContent = `Request failed: ${error.message}`;
      } finally {
        sendButton.disabled = false;
      }
    });

    startRuntimeButton.addEventListener("click", async () => {
      runtimeStatusNode.textContent = "Starting runtime...";
      try {
        const payload = await callEndpoint("/runtime/start");
        runtimeStatusNode.textContent = `Runtime running: ${payload.running}`;
      } catch (error) {
        runtimeStatusNode.textContent = `Start failed: ${error.message}`;
      }
    });

    stopRuntimeButton.addEventListener("click", async () => {
      runtimeStatusNode.textContent = "Stopping runtime...";
      try {
        const payload = await callEndpoint("/runtime/stop");
        runtimeStatusNode.textContent = `Runtime running: ${payload.running}`;
      } catch (error) {
        runtimeStatusNode.textContent = `Stop failed: ${error.message}`;
      }
    });

    resetStateButton.addEventListener("click", async () => {
      runtimeStatusNode.textContent = "Resetting state...";
      try {
        const payload = await callEndpoint("/reset");
        lastSpeechSignature = null;
        chatLog.length = 0;
        shotHistory.length = 0;
        chatLogNode.innerHTML = "";
        renderSnapshot(payload.snapshot);
        runtimeStatusNode.textContent = "State reset.";
      } catch (error) {
        runtimeStatusNode.textContent = `Reset failed: ${error.message}`;
      }
    });

    connect();
  </script>
</body>
</html>
        """
    )


@app.get("/state")
def state() -> dict:
    return logic().get_state()


@app.post("/reset")
async def reset() -> dict:
    result = logic().reset_state()
    await runtime_control.broadcast(result["snapshot"])
    return result


@app.post("/tick")
async def tick() -> dict:
    result = logic().tick_world()
    await runtime_control.broadcast(result["snapshot"])
    return result


@app.post("/runtime/start")
async def runtime_start() -> dict:
    return await runtime_control.start_runtime()


@app.post("/runtime/stop")
async def runtime_stop() -> dict:
    return await runtime_control.stop_runtime()


@app.get("/runtime/status")
def runtime_status() -> dict:
    return runtime_control.status()


@app.post("/process")
async def process(payload: ProcessRequest) -> dict:
    result = logic().process_message(payload.text)
    await runtime_control.broadcast(result["snapshot"])
    return result


@app.websocket("/ws")
async def websocket_runtime(websocket: WebSocket) -> None:
    await websocket.accept()
    queue = runtime_control.subscribe()

    try:
        await runtime_control.push_current_state(queue)
        while True:
            message = await queue.get()
            await websocket.send_json(message)
    except WebSocketDisconnect:
        runtime_control.unsubscribe(queue)
    finally:
        runtime_control.unsubscribe(queue)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
