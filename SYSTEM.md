# SYSTEM.md — Courtroom AI

Technical/architectural reference. For a plain-English tour of *what this does*, see the README.

---

## 1. Repository layout

```
courtroom_simulation_api/
├── backend/
│   ├── main.py                    FastAPI app; /simulate (SSE), /simulate/full, /health
│   ├── llm.py                      LLM caller: Groq or Ollama, mock mode, Langfuse tracing
│   ├── config.py                    loads config.yaml -> per-agent AgentConfig (model, call_type, max_tokens)
│   ├── config.yaml                   per-agent model/call-type overrides
│   ├── graph/
│   │   ├── state.py                    CourtState (TypedDict) — the single shared state object
│   │   └── graph.py                     build_graph() — LangGraph node wiring, fixed sequential edges
│   └── agents/                        one file per agent, one function per agent
│       ├── case_manager.py, legal_research.py, consultant.py, top_consultant.py,
│       ├── prosecutor.py (2 functions: r1, r2), defense.py (2 functions: r1, r2),
│       ├── judge.py, reporter.py, web_search.py
│       └── schemas.py                  Pydantic: CaseIntake, ApplicableSection, Precedent,
│                                          LegalResearch, JudgeVerdict
└── frontend/
    ├── app.py                          Streamlit: complaint input, live SSE-driven agent cards,
    │                                     report export, links to the Metrics tab
    └── evaluation/
        ├── evaluator.py                  local, non-LLM heuristic scoring of a finished run
        └── dashboard.py                   renders evaluator.py's scores in Streamlit
```

**Reading order:** `graph/state.py` → `graph/graph.py` → any one `agents/*.py` file → `main.py`. That's the whole system; every agent file follows the same shape (read `CourtState`, call `llm.py`, return a partial state dict).

---

## 2. The state object: `CourtState`

A single `TypedDict` (not a class with methods — just a typed dict) holds every field any agent might read or write: `complaint`, the Case Manager's structured `case_intake` (plus flattened `entities`/`accused`/`offence`/`victim`/`facts` strings kept for backwards-compatible export), Legal Research's `legal_research` dict, each argument round (`pros_r1`, `def_r1`, `pros_r2`, `def_r2`), the Judge's `judge_verdict` dict (plus flattened `verdict`/`confidence`/`reasoning`/`probable_punishment`), and the Reporter's `headline`/`report`.

Every agent function has the same shape: `(state: CourtState) -> dict` — it reads whatever fields it needs and returns only the *new* fields it's contributing (LangGraph merges this partial dict into the running state). No agent mutates state in place or reaches into fields it doesn't own.

**Why both a structured dict and a flattened string exist for the same data** (e.g. `case_intake` *and* `entities`/`accused`/`facts`): the structured Pydantic-validated dict (`case_intake`, `legal_research`, `judge_verdict`) is what the UI should render from — reliable, typed fields. The flattened strings exist purely for export/back-compat with older code paths that expected plain text. New code should read the structured dicts, not the flattened strings.

---

## 3. The graph: fixed sequence, not a branching machine

`graph/graph.py::build_graph()` registers 10 nodes and wires them with **plain sequential edges** — `case_manager → legal_research → consultant → prosecutor_r1 → defense_r1 → prosecutor_r2 → defense_r2 → judge → reporter → top_consultant → END`. There is no conditional branching, no loop-back, no node that decides what runs next based on content. LangGraph is used here purely as a state-machine runner with tracing/streaming support built in — not for its graph-branching capabilities.

```
case_manager → legal_research → consultant → prosecutor_r1 → defense_r1
     → prosecutor_r2 → defense_r2 → judge → reporter → top_consultant → END
```

Note the registration order in code lists `top_consultant` differently from its edge position — it's wired in as the **last** node (after `reporter`), serving as a closing executive-level review of the entire finished case, not an early-stage consultant call.

---

## 4. Two call shapes, one LLM caller

`agents/schemas.py` documents the split directly: **structured** calls (Case Manager, Legal Research, Judge) validate the model's JSON output against a Pydantic schema via `call_structured()`; everything else (Consultant, Top Consultant, Prosecutor, Defense, Reporter) is free-form prose via a plain text-completion call. Both paths go through the same underlying `llm.py`.

`llm.py` supports two providers behind one interface — `LLM_PROVIDER=groq` (default) or `LLM_PROVIDER=ollama` (a local model, via an OpenAI-compatible endpoint) — plus a `MOCK_LLM=true` escape hatch for running the graph with no LLM calls at all (useful for testing the graph wiring/streaming without spending API quota). Per-agent model overrides come from `config.yaml` via `Config.get_model(agent_name)`; if an agent isn't listed there, it silently falls back to the default model rather than failing.

---

## 5. Streaming architecture: bridging sync LangGraph with async FastAPI

This is the trickiest piece of the backend and worth understanding if debugging streaming issues. `court_graph.stream(...)` is **blocking, synchronous** code. Running it directly inside an `async def` route would freeze the entire event loop (including the server's ability to handle other requests or `Ctrl+C`) for the whole simulation. The fix in `main.py::simulate()`:

```
1. Spin up a background daemon thread that runs court_graph.stream()
2. Each node's output update gets pushed onto a thread-safe queue.Queue
3. The async route polls that queue with asyncio.to_thread(queue.get, timeout=300)
4. Each item pulled off the queue is yielded immediately as an SSE "agent" event
5. A sentinel value signals completion; a caught exception is relayed as an "error" event
6. A 300-second queue-get timeout guards against a truly stuck simulation
```

`/simulate/full` sidesteps all of this by running `court_graph.invoke()` (blocking, returns the complete final state) inside `asyncio.to_thread(...)` and just awaiting the result — the simpler non-streaming path, used when a client doesn't need live progress.

---

## 6. Observability: two separate systems, easy to conflate

- **Langfuse tracing** (`llm.py`, `main.py`) wraps the entire simulation in one parent trace (`courtroom-simulation`) with every individual agent's LLM call nested underneath — exact prompt, response, latency, token usage. This is infrastructure-level observability: it tells you what happened during a run, not whether the legal reasoning was any good.
- **`frontend/evaluation/evaluator.py`** is a completely separate, local, non-LLM scoring system that runs against a *finished* simulation's output and scores completeness/coherence/rough legal accuracy using heuristics — no additional model call, no dependency on Langfuse. `dashboard.py` just renders whatever `evaluator.py` computes.

These share no code and answer different questions; don't assume one substitutes for the other.

---

## 7. Legal framework grounding

Agent system prompts (see `agents/case_manager.py`, `agents/legal_research.py`) are explicitly written around India's 2023 criminal-law codification — the **Bharatiya Nyaya Sanhita (BNS)**, **Bharatiya Nagarik Suraksha Sanhita (BNSS)**, and **Bharatiya Sakshya Adhiniyam (BSA)** — which replaced the older IPC/CrPC/Indian Evidence Act. This is baked into prompt text, not configurable via an env var — swapping to a different jurisdiction's legal framework would mean editing prompts in each agent file, not a config change.

---

## 8. Known shortcomings / things to be aware of

- **No persistence at all.** `CourtState` lives only in the request's in-memory scope for the duration of one `/simulate` or `/simulate/full` call. There is no session store, no database, no way to resume or revisit a past simulation once the response stream ends — the frontend must hold onto whatever it received if the user wants to look back at it.
- **No auth.** `main.py` sets `allow_origins=["*"]` and there's no API-key gate on the backend (unlike ClusterMaster's `X-API-Key` header) — this is meant to run trusted/local, not exposed directly to the public internet.
- **Fixed pipeline, no error recovery mid-run.** If one agent's structured-output call fails to validate against its Pydantic schema partway through, there's no retry/repair step visible in the graph wiring — an exception surfaces as an SSE `"error"` event and the whole run stops; a user must resubmit the complaint from scratch.
- **`llm.py`'s default model differs from other configs** — `DEFAULT_GROQ_MODEL` here is `llama-3.1-8b-instant`, while `config.py`'s module-level `DEFAULT_MODEL` reads `llama-3.3-70b-versatile` from the same `GROQ_MODEL` env var. Which one actually applies depends on whether `config.get_model(agent_name)` successfully returns a per-agent override — worth checking closely if you're trying to pin down exactly which model an agent used.
- **Two "consultant" agents with easy-to-confuse names.** `consultant.py` (early, quick strategic read) and `top_consultant.py` (final, closing executive review) sound similar but run at opposite ends of the pipeline — this is intentional but easy to misread in the graph definition or state fields.
- **Legal accuracy is not guaranteed.** Legal Research is web-search-assisted (Tavily) but nothing verifies its citations against an authoritative legal database — precedents and sections should be treated as a starting point for verification, not a citation you can rely on directly.
- **No rate limiting / cost controls.** Each `/simulate` call triggers roughly 10 sequential LLM calls (more if Legal Research issues multiple searches); there's no built-in cap on concurrent simulations or per-IP throttling.
