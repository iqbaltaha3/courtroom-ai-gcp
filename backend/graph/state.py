from typing import TypedDict, Optional


class CourtState(TypedDict):
    # ── Input ──────────────────────────────────────────
    complaint: str

    # ── Agent 1: Case Manager ──────────────────────────
    entities: Optional[str]        # flattened text (for export/back-compat)
    accused: Optional[str]
    offence: Optional[str]
    victim: Optional[str]
    facts: Optional[str]           # flattened "; "-joined string
    case_intake: Optional[dict]    # CaseIntake.model_dump() — structured, use this in UI

    # ── Agent 2: Legal Research ────────────────────────
    laws: Optional[str]            # flattened text (for export/back-compat)
    sections_applied: Optional[str]
    precedents: Optional[str]
    legal_research: Optional[dict]  # LegalResearch.model_dump() — structured, use this in UI

    # ── Agent 3: Internal Consultant ───────────────────
    consultant: Optional[str]      # neutral advisory note for strategy/evidence

    # ── Agent 3B: Consultant Sparrow ───────────────────
    top_consultant: Optional[str]  # independent high-level advisory review

    # ── Agent 4 & 5: Round 1 ──────────────────────────
    pros_r1: Optional[str]
    def_r1: Optional[str]

    # ── Agent 6 & 7: Round 2 ──────────────────────────
    pros_r2: Optional[str]
    def_r2: Optional[str]

    # ── Agent 8: Judge ─────────────────────────────────
    verdict: Optional[str]         # flattened full verdict text (for export/back-compat)
    verdict_short: Optional[str]   # Guilty / Not Guilty / Partial
    confidence: Optional[int]      # 0-100
    reasoning: Optional[str]
    probable_punishment: Optional[str]
    judge_verdict: Optional[dict]  # JudgeVerdict.model_dump() — structured, use this in UI

    # ── Agent 9: Reporter ──────────────────────────────
    headline: Optional[str]
    report: Optional[str]          # journalistic summary