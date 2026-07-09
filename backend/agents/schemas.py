"""
Pydantic schemas for agent outputs that need structured fields.

Only agents whose output naturally decomposes into discrete fields use
these (case manager, legal research, judge). Prosecutor, defense, and
reporter produce free-form persuasive/journalistic prose — forcing a
rigid schema onto that kind of writing degrades quality for no benefit,
so they keep using the plain call_claude() text path.
"""

from pydantic import BaseModel, Field
from typing import Literal


class CaseIntake(BaseModel):
    """Structured output for the Case Manager agent."""
    accused: str = Field(description="Name(s) of accused person(s) or entities, or 'Unknown' if not stated")
    victim: str = Field(description="Name(s) of alleged victim(s)/complainant(s), or 'Unknown' if not stated")
    allegation: str = Field(description="Neutral one-line summary of what is alleged to have happened")
    offences: str = Field(description="Apparent offence(s) suggested by the facts, stated neutrally")
    jurisdiction: str = Field(description="Apparent court/territorial jurisdiction, or 'Unknown'")
    facts: list[str] = Field(description="Chronological list of material facts extracted from the complaint")
    missing_information: list[str] = Field(
        default_factory=list,
        description="Important information that is absent from the complaint and may matter later"
    )


class ApplicableSection(BaseModel):
    """A single statutory provision identified as potentially relevant."""
    section: str = Field(description="Section number, e.g. 'Section 316'")
    act: str = Field(description="Name of the Act, e.g. 'Bharatiya Nyaya Sanhita, 2023'")
    relevance: str = Field(description="Why this section may be relevant to the facts presented")


class Precedent(BaseModel):
    """A single judicial precedent identified as potentially relevant."""
    case_name: str = Field(description="Name of the case")
    court: str = Field(description="Court that decided it, e.g. 'Supreme Court of India'")
    year: str = Field(description="Year of the decision")
    relevance: str = Field(description="The legal principle established and its relevance to the present facts")


class LegalResearch(BaseModel):
    """Structured output for the Legal Research agent."""
    applicable_sections: list[ApplicableSection] = Field(
        description="Statutory provisions plausibly applicable to the facts"
    )
    precedents: list[Precedent] = Field(
        default_factory=list,
        description="Judicial precedents plausibly relevant to the facts"
    )
    evidentiary_notes: list[str] = Field(
        default_factory=list,
        description="Notes on applicable evidentiary provisions (Bharatiya Sakshya Adhiniyam), admissibility, or evidentiary gaps"
    )
    unsettled_questions: list[str] = Field(
        default_factory=list,
        description="Open or unsettled questions of law, or areas requiring further factual development"
    )


class JudgeVerdict(BaseModel):
    """Structured output for the Judge agent."""
    verdict: Literal["Guilty", "Not Guilty", "Partially Liable"] = Field(description="The judge's verdict")
    reasoning: str = Field(description="The judge's reasoning for the verdict, in natural judicial language")
    sections_applied: list[str] = Field(default_factory=list, description="Statutory sections applied")
    probable_punishment: str = Field(default="", description="Likely consequence if guilty (imprisonment, fine, compensation)")
    confidence: int = Field(ge=0, le=100, description="Confidence level (0-100)")