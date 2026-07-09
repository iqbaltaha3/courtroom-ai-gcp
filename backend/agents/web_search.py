"""
Web search utility for legal research using Tavily.
Enables the legal research agent to find current laws, precedents, and case law.
"""

import os
from tavily import TavilyClient

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def search_legal_precedents(query: str, offence: str) -> str:
    """
    Search for judicial precedents, case law, and legal interpretations.
    
    Args:
        query: The search query (e.g., facts from the case)
        offence: The alleged offence (e.g., "theft under BNS 304")
    
    Returns:
        Formatted string of search results with case names, courts, and relevance
    """
    search_query = f"Indian law {offence} precedent case law Supreme Court High Court {query}"
    
    try:
        results = tavily.search(query=search_query, max_results=5, include_answer=False)
        
        if not results.get("results"):
            return "No precedents found in search."
        
        precedents_text = "SEARCH RESULTS - Judicial Precedents & Case Law:\n"
        for i, result in enumerate(results["results"], 1):
            precedents_text += f"\n{i}. {result.get('title', 'Unknown Case')}\n"
            precedents_text += f"   Source: {result.get('source', 'Unknown')}\n"
            precedents_text += f"   Context: {result.get('content', '')[:200]}...\n"
        
        return precedents_text
    except Exception as e:
        return f"Web search error: {str(e)}"


def search_applicable_laws(offence: str, allegation: str) -> str:
    """
    Search for applicable statutory provisions and legal sections.
    
    Args:
        offence: The alleged offence
        allegation: Brief summary of allegation
    
    Returns:
        Formatted string of applicable laws and statutory provisions
    """
    search_query = f"Bharatiya Nyaya Sanhita BNS 2023 {offence} {allegation} section"
    
    try:
        results = tavily.search(query=search_query, max_results=5, include_answer=False)
        
        if not results.get("results"):
            return "No applicable laws found in search."
        
        laws_text = "SEARCH RESULTS - Applicable Laws & Sections:\n"
        for i, result in enumerate(results["results"], 1):
            laws_text += f"\n{i}. {result.get('title', 'Unknown Law')}\n"
            laws_text += f"   Source: {result.get('source', 'Unknown')}\n"
            laws_text += f"   Summary: {result.get('content', '')[:200]}...\n"
        
        return laws_text
    except Exception as e:
        return f"Web search error: {str(e)}"


def search_evidentiary_requirements(offence: str, facts: list) -> str:
    """
    Search for evidentiary requirements and proof standards for the alleged offence.
    
    Args:
        offence: The alleged offence
        facts: List of material facts from the case
    
    Returns:
        Formatted string of evidentiary requirements and legal standards
    """
    key_facts = " ".join(facts[:3]) if facts else ""
    search_query = f"Bharatiya Sakshya Adhiniyam 2023 evidence {offence} proof requirements {key_facts}"
    
    try:
        results = tavily.search(query=search_query, max_results=4, include_answer=False)
        
        if not results.get("results"):
            return "No evidentiary information found in search."
        
        evidence_text = "SEARCH RESULTS - Evidentiary Requirements:\n"
        for i, result in enumerate(results["results"], 1):
            evidence_text += f"\n{i}. {result.get('title', 'Unknown')}\n"
            evidence_text += f"   Source: {result.get('source', 'Unknown')}\n"
            evidence_text += f"   Details: {result.get('content', '')[:200]}...\n"
        
        return evidence_text
    except Exception as e:
        return f"Web search error: {str(e)}"
