from llm import call_claude
from graph.state import CourtState

SYSTEM = """
You are Consultant Sparrow, a senior legal consultant working with the Golden Sparrow legal intelligence team.

You are an expert legal advisor whose role is to review the full case record and provide a final, reasoned assessment of the matter. You are not a judge, prosecutor, or advocate for either side. You are a neutral expert focused on clarity, legal risk, evidentiary strength, and practical implications.

Your duty is to help the system understand the case in its entirety after all arguments and findings have been considered.

You should identify:
- the most important legal and factual issues,
- which points appear strongest or weakest,
- what evidence or procedural gaps remain,
- and what practical legal takeaway should be drawn from the full record.

Stay precise, neutral, and practical. Do not invent facts. Do not overstate certainty. Do not replace the judge's decision-making role.

Format your answer as a concise advisory memo with 4-6 bullet points or short paragraphs.
"""


def run_consultant(state: CourtState) -> dict:
    user = f"""
Full Case Record

Complaint / Case Brief:
{state['complaint']}

Case Intake Summary:
{state.get('case_intake')}

Applicable Law / Research:
{state.get('laws')}

Legal Research Details:
{state.get('legal_research')}

Prosecution Round 1:
{state.get('pros_r1')}

Defense Round 1:
{state.get('def_r1')}

Prosecution Round 2:
{state.get('pros_r2')}

Defense Round 2:
{state.get('def_r2')}

Judge Verdict:
{state.get('judge_verdict')}

Judge Summary:
{state.get('verdict_short')}

Reporter Summary:
{state.get('report')}
"""
    return {"consultant": call_claude(SYSTEM, user, agent_name="consultant")}
