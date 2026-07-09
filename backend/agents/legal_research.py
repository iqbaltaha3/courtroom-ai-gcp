from llm import call_structured
from agents.schemas import LegalResearch
from agents.web_search import search_applicable_laws, search_legal_precedents, search_evidentiary_requirements
from graph.state import CourtState

SYSTEM = """
You are Ananya, a Senior Legal Research Officer attached to a High Court research cell.

You have 15 years of experience conducting legal research for judges, senior advocates, public prosecutors, and government departments.

You possess expert knowledge of:

• Bharatiya Nyaya Sanhita, 2023 (BNS)
• Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)
• Bharatiya Sakshya Adhiniyam, 2023 (BSA)
• Constitution of India
• Supreme Court jurisprudence
• High Court jurisprudence
• Statutory interpretation
• Principles of criminal and civil law

You have access to live web search results for current case law, precedents, and statutory interpretations. Use these results as supporting material, but apply your own legal judgment. Verify any citations and ensure they are accurately attributed.

ROLE

You are not a prosecutor.

You are not defence counsel.

You are not the judge.

You do not argue guilt, innocence, conviction, acquittal, liability, or punishment.

Your sole responsibility is to identify and explain the law that may be relevant to the facts presented.

You function as a neutral legal research officer assisting the Court.

RESEARCH PRINCIPLES

• Identify legal issues arising from the facts.

• Identify statutory provisions that may apply.

• Identify the essential ingredients of each provision.

• Identify relevant procedural provisions where applicable.

• Identify relevant constitutional provisions.

• Identify leading precedents from the Supreme Court and High Courts.

• Explain why each authority may be relevant.

• Distinguish authorities that appear relevant but may not squarely apply.

• Identify conflicts in precedent when they exist.

• Note unsettled questions of law.

• Never assume facts that have not been provided.

• Never invent statutes, sections, precedents, or legal principles.

• Use web search results to enhance accuracy and currency of precedents.

ANALYTICAL APPROACH

For every legal issue:

1. Identify the issue.
2. Identify the governing statutory provision.
3. Explain the legal ingredients or requirements.
4. Identify relevant judicial precedents (from both traditional knowledge and web search results).
5. Explain the relevance of those precedents.
6. Note competing interpretations if they exist.
7. Identify areas requiring further factual development.

PRECEDENT ANALYSIS

When citing a precedent, state the case name, the court, the year, the legal
principle established, and its relevance to the present facts. Do not merely
list authorities — explain why they matter. Prioritize recent and binding precedents.

EVIDENTIARY ANALYSIS

Where evidence is relevant, identify the applicable provisions of the
Bharatiya Sakshya Adhiniyam, distinguish admissibility from evidentiary
weight, note what evidence would be required to establish the legal
ingredients of an offence or claim, and identify evidentiary gaps.

Identify ONLY laws that are plausibly applicable.

Do not invent facts.
Do not argue guilt.
Do not give conclusions.
Only identify applicable law.

OUTPUT CONSTRAINTS

• Identify ONLY the 3-4 most relevant statutory sections (omit marginally applicable ones).
• For each section, provide ONE brief sentence of relevance (not detailed explanations).
• Include at most 2-3 precedents (prioritize recent & binding ones only).
• Keep evidentiary_notes to 2-3 key points maximum.
• Keep unsettled_questions brief if included (optional).
"""


def run_legal_research(state: CourtState) -> dict:
    # Truncate complaint more aggressively to avoid token limits
    MAX_COMPLAINT_CHARS = 1500
    complaint = state['complaint']
    if len(complaint) > MAX_COMPLAINT_CHARS:
        complaint = complaint[:MAX_COMPLAINT_CHARS] + "\n\n[... truncated ...]"
    
    # state['facts'] is a "; "-joined string (see case_manager.py), not a
    # list — split it back into a list before slicing to the first 3 facts.
    facts_raw = state.get('facts') or ""
    facts_for_search = [f.strip() for f in facts_raw.split(";") if f.strip()][:3]

    # Perform web searches to enrich the research with current precedents and laws
    allegation = (state.get('case_intake') or {}).get('allegation', '')
    laws_search = search_applicable_laws(state['offence'], allegation)
    # Limit to first 2000 chars of web search results
    laws_search = laws_search[:2000] if laws_search else ""
    
    precedents_search = search_legal_precedents(
        " ".join(facts_for_search) if facts_for_search else complaint[:500],
        state['offence']
    )
    # Limit to first 1500 chars
    precedents_search = precedents_search[:1500] if precedents_search else ""
    
    evidence_search = search_evidentiary_requirements(state['offence'], facts_for_search)
    # Limit to first 1000 chars
    evidence_search = evidence_search[:1000] if evidence_search else ""
    
    user = f"""
Complaint (key facts only):
{complaint}

Accused: {state['accused']}
Victim: {state['victim']}
Alleged Offence: {state['offence']}

Facts:
{chr(10).join(f'- {f}' for f in facts_for_search) if facts_for_search else 'None provided'}

---

WEB SEARCH CONTEXT (Use to enhance research):

{laws_search}

{precedents_search}

{evidence_search}

---

Based on the facts, web search results, and your legal expertise, identify the applicable laws, relevant precedents, and evidentiary requirements.
"""

    result: LegalResearch = call_structured(SYSTEM, user, LegalResearch, max_tokens=1500,
                                               agent_name="legal_research")

    # ── Reconstruct readable text blocks ────────────────────────────
    # Downstream agents (prosecutor, defense, judge) interpolate
    # state['laws'] directly into their own prompts as prose, and app.py
    # displays it as a text block — so we rebuild a clean formatted
    # version from the structured data rather than changing every
    # consumer's prompt/UI code.

    sections_lines = []
    for i, s in enumerate(result.applicable_sections, 1):
        sections_lines.append(f"{i}. {s.section} | {s.act}\n   Relevance: {s.relevance}")
    sections_text = "\n\n".join(sections_lines) if sections_lines else "None identified."

    precedents_lines = []
    for i, p in enumerate(result.precedents, 1):
        precedents_lines.append(f"{i}. {p.case_name} | {p.court} | {p.year}\n   Relevance: {p.relevance}")
    precedents_text = "\n\n".join(precedents_lines) if precedents_lines else "None identified."

    evidentiary_text = (
        "\n".join(f"- {n}" for n in result.evidentiary_notes)
        if result.evidentiary_notes else "None noted."
    )
    unsettled_text = (
        "\n".join(f"- {q}" for q in result.unsettled_questions)
        if result.unsettled_questions else "None noted."
    )

    full_text = f"""APPLICABLE SECTIONS:
{sections_text}

PRECEDENTS:
{precedents_text}

EVIDENTIARY NOTES:
{evidentiary_text}

UNSETTLED QUESTIONS:
{unsettled_text}"""

    # Compact one-line-per-item versions for the sections_applied /
    # precedents fields, matching what app.py expects to display.
    sections_compact = "; ".join(f"{s.section}, {s.act}" for s in result.applicable_sections) or "Unknown"
    precedents_compact = "; ".join(
        f"{p.case_name} ({p.court}, {p.year})" for p in result.precedents
    ) or "Unknown"

    return {
        "laws": full_text,
        "sections_applied": sections_compact,
        "precedents": precedents_compact,
        "legal_research": result.model_dump(),
    }