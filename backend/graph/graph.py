from langgraph.graph import StateGraph, END

from graph.state import CourtState
from agents.case_manager   import run_case_manager
from agents.legal_research  import run_legal_research
from agents.consultant      import run_consultant
from agents.top_consultant  import run_top_consultant
from agents.prosecutor      import run_prosecutor_r1, run_prosecutor_r2
from agents.defense         import run_defense_r1,   run_defense_r2
from agents.judge           import run_judge
from agents.reporter        import run_reporter


def build_graph() -> StateGraph:
    g = StateGraph(CourtState)

    # ── Register nodes ──────────────────────────────────
    g.add_node("case_manager",   run_case_manager)
    g.add_node("legal_research", run_legal_research)
    g.add_node("consultant",     run_consultant)
    g.add_node("prosecutor_r1",  run_prosecutor_r1)
    g.add_node("defense_r1",     run_defense_r1)
    g.add_node("prosecutor_r2",  run_prosecutor_r2)
    g.add_node("defense_r2",     run_defense_r2)
    g.add_node("judge",          run_judge)
    g.add_node("reporter",       run_reporter)
    g.add_node("top_consultant", run_top_consultant)

    # ── Sequential edges ────────────────────────────────
    g.set_entry_point("case_manager")
    g.add_edge("case_manager",   "legal_research")
    g.add_edge("legal_research", "consultant")
    g.add_edge("consultant",     "prosecutor_r1")
    g.add_edge("prosecutor_r1",  "defense_r1")
    g.add_edge("defense_r1",     "prosecutor_r2")
    g.add_edge("prosecutor_r2",  "defense_r2")
    g.add_edge("defense_r2",     "judge")
    g.add_edge("judge",          "reporter")
    g.add_edge("reporter",       "top_consultant")
    g.add_edge("top_consultant", END)

    return g.compile()


# Singleton — import this everywhere
court_graph = build_graph()
