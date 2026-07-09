# Courtroom AI — Legal Simulation

A multi-agent courtroom simulation (case manager → legal research → consultant →
prosecution/defense rounds → judge → reporter) built with LangGraph, running on Groq.

## Architecture

```
courtroom_simulation/
├── backend/            FastAPI backend — runs the LangGraph simulation, streams
│   ├── main.py           results over SSE, exposes /simulate and /simulate/full
│   ├── llm.py             Groq API caller (with Langfuse tracing)
│   ├── config.py          loads config.yaml, reads GROQ_API_KEY / GROQ_MODEL
│   ├── config.yaml         per-agent settings (call type, max tokens)
│   ├── agents/              one file per courtroom agent
│   └── graph/                LangGraph state + graph wiring
└── frontend/           Streamlit UI — calls the backend, renders the stream
    └── app.py
```

The frontend has no simulation logic in it — it just posts the complaint to the
backend and displays whatever comes back over SSE. All the LLM/graph logic lives
in the backend, so you can swap the frontend (or call the API directly) without
touching agent code.

## Setup

1. **Backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env
   # then edit .env and add your GROQ_API_KEY (and TAVILY_API_KEY for web search)
   uvicorn main:app --reload --port 8000
   ```

2. **Frontend** (in a second terminal)
   ```bash
   cd frontend
   pip install -r requirements.txt
   streamlit run app.py
   ```
   The frontend expects the backend at `http://localhost:8000` by default —
   override with the `BACKEND_URL` env var if needed.

## LLM Provider

This project uses **Groq only**, one model for all agents by default
(`GROQ_MODEL` in `.env`, defaults to `llama-3.3-70b-versatile`). If you want a
different model for a specific agent (e.g. a stronger model for the judge),
add a `model:` field for that agent in `backend/config.yaml`.

## Observability (Langfuse)

Every LLM call and the whole simulation run are traced to Langfuse automatically.
1. Sign up at [cloud.langfuse.com](https://cloud.langfuse.com) (or self-host) and
   grab your public/secret keys.
2. Add them to `backend/.env`:
   ```
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
   LANGFUSE_BASE_URL=https://cloud.langfuse.com
   ```
3. Run a simulation — traces (one per run, with every agent's Groq call nested
   underneath) show up in your Langfuse project dashboard automatically.

If you leave the Langfuse keys blank, nothing breaks — tracing is just skipped.

## API

- `POST /simulate` — streams each agent's output as Server-Sent Events (used by the frontend)
- `POST /simulate/full` — runs the full simulation and returns the final state as JSON
- `GET /health` — checks that `GROQ_API_KEY` is configured

## What changed from the previous version

- **LLM provider**: OpenRouter removed — Groq is now the only provider, one model
  for everything by default (see `backend/config.yaml` to override per agent).
- **Architecture**: split into a FastAPI backend (`backend/`) and a thin Streamlit
  frontend (`frontend/`) that only calls the backend API — no more direct
  `graph.invoke()` calls from Streamlit.
- **Observability**: added Langfuse tracing around every LLM call and each full run.
- **Bug fix**: `legal_research.py` was slicing `state['facts']` (a string) as if
  it were a list, which fed individual characters into the web search queries
  instead of the actual facts. Fixed to split the string back into a list first.
- **Cleanup**: removed the old monolithic `app.py` (1300+ lines of Streamlit +
  business logic mixed together), duplicate/legacy config files (`config.py.old`,
  `config_cli.py.old`, `config_simple.py`, `agents_simple.py`), the OpenRouter
  provider-switch example, and ~10 redundant summary/guide markdown files.
