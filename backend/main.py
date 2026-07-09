"""
Courtroom AI — FastAPI backend.

Runs the LangGraph courtroom simulation and streams each agent's output
back to the frontend over Server-Sent Events (SSE).

Run with:  uvicorn main:app --reload --port 8000
"""

import json
import asyncio
import queue
import threading
import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from langfuse import observe, get_client

from config import config
from graph.graph import court_graph

app = FastAPI(title="Courtroom AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _empty_state(complaint: str) -> dict:
    return {
        "complaint": complaint,
        "entities": None, "accused": None, "offence": None, "victim": None,
        "facts": None, "case_intake": None,
        "laws": None, "sections_applied": None, "precedents": None,
        "legal_research": None,
        "consultant": None,
        "top_consultant": None,
        "pros_r1": None, "def_r1": None,
        "pros_r2": None, "def_r2": None,
        "verdict": None, "verdict_short": None,
        "confidence": None, "reasoning": None, "probable_punishment": None,
        "judge_verdict": None,
        "headline": None, "report": None,
    }


class SimulateRequest(BaseModel):
    complaint: str


@app.get("/health")
def health():
    ok, message = config.validate_setup()
    return {"ok": ok, "message": message}


@app.post("/simulate")
async def simulate(req: SimulateRequest):
    """Stream each agent's output as Server-Sent Events."""

    async def event_stream():
        initial_state = _empty_state(req.complaint)
        langfuse = get_client()

        # court_graph.stream() is blocking sync code. Running it directly
        # inside this async generator would freeze uvicorn's event loop
        # (including Ctrl+C handling) for the whole simulation. Instead we
        # run it in a background thread and relay events through a queue,
        # polling with a short timeout so the loop stays responsive.
        event_queue: "queue.Queue" = queue.Queue()
        SENTINEL_DONE = object()

        def run_graph():
            try:
                with langfuse.start_as_current_observation(
                    as_type="span", name="courtroom-simulation"
                ) as root_span:
                    root_span.update(input={"complaint": req.complaint})
                    for update in court_graph.stream(initial_state, stream_mode="updates"):
                        event_queue.put(("update", update))
                event_queue.put((SENTINEL_DONE, None))
            except Exception:
                event_queue.put(("error", traceback.format_exc()))

        thread = threading.Thread(target=run_graph, daemon=True)
        thread.start()

        try:
            while True:
                try:
                    kind, payload = await asyncio.to_thread(event_queue.get, True, 300)
                except queue.Empty:
                    yield {"event": "error", "data": json.dumps({"error": "Simulation timed out."})}
                    break

                if kind == SENTINEL_DONE:
                    yield {"event": "done", "data": json.dumps({"status": "complete"})}
                    break

                if kind == "error":
                    yield {"event": "error", "data": json.dumps({"error": payload})}
                    break

                # kind == "update": payload is {node_name: partial_state_dict}
                # Send it through as-is — the frontend merges partial_state_dict
                # straight into its own state, same as court_graph.stream() would
                # give it in-process. No field is dropped or renamed here.
                yield {"event": "agent", "data": json.dumps(payload)}
        except asyncio.CancelledError:
            # Client disconnected — let the background thread finish on its
            # own (it's a daemon thread so it won't block server shutdown).
            raise

    return EventSourceResponse(event_stream())


@app.post("/simulate/full")
async def simulate_full(req: SimulateRequest):
    """Non-streaming: return complete final state as JSON."""
    initial_state = _empty_state(req.complaint)
    result = await asyncio.to_thread(court_graph.invoke, initial_state)
    return result