"""
LLM caller for Courtroom AI — supports Groq and local Ollama.
Switch via environment variable LLM_PROVIDER = "groq" | "ollama".
For testing without any LLM, set MOCK_LLM=true.
"""

import json
import os
from typing import Type, TypeVar, Any, Dict

from openai import OpenAI
from pydantic import BaseModel
from langfuse import observe, get_client

# We keep config for validation and per‑agent model lookups if needed
from config import config

T = TypeVar("T", bound=BaseModel)

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
MOCK_LLM = os.getenv("MOCK_LLM", "false").lower() == "true"
PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()  # "groq" or "ollama"

# Groq settings
GROQ_API_KEY = config.groq_api_key  # from config
# If you want per‑agent models, we'll use config.get_model(agent_name) later.
# For the client, we only need a default fallback.
DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Ollama settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "ollama")  # dummy key

# ------------------------------------------------------------
# Clients (lazy init)
# ------------------------------------------------------------
_groq_client = None
_ollama_client = None

def get_groq_client():
    global _groq_client
    if _groq_client is None:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set for Groq provider.")
        _groq_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
    return _groq_client

def get_ollama_client():
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OpenAI(api_key=OLLAMA_API_KEY, base_url=OLLAMA_BASE_URL)
    return _ollama_client

def get_client_and_model(agent_name: str = None):
    """
    Return the appropriate client and the model name to use.
    If agent_name is provided, and we are using Groq, we can look up
    a custom model from config. Otherwise, fallback to defaults.
    """
    if MOCK_LLM:
        return None, None
    if PROVIDER == "groq":
        client = get_groq_client()
        # Use per‑agent model if config provides it, else default
        try:
            model = config.get_model(agent_name) if agent_name else DEFAULT_GROQ_MODEL
        except TypeError:
            # In case config.get_model still needs an argument
            model = DEFAULT_GROQ_MODEL
        return client, model
    elif PROVIDER == "ollama":
        return get_ollama_client(), OLLAMA_MODEL
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {PROVIDER}")

# ------------------------------------------------------------
# Mock data generators (used when MOCK_LLM=true)
# ------------------------------------------------------------
def _dummy_structured_data(schema: Type[T]) -> Dict[str, Any]:
    dummy = {}
    for field_name, field_info in schema.model_fields.items():
        if field_info.annotation == str:
            dummy[field_name] = f"dummy_{field_name}"
        elif field_info.annotation in (int, float):
            dummy[field_name] = 0
        elif field_info.annotation == bool:
            dummy[field_name] = False
        elif hasattr(field_info.annotation, "__origin__") and field_info.annotation.__origin__ is list:
            dummy[field_name] = []
        elif hasattr(field_info.annotation, "__origin__") and field_info.annotation.__origin__ is dict:
            dummy[field_name] = {}
        else:
            dummy[field_name] = None
    return dummy

def _dummy_prose_response(agent_name: str = None) -> str:
    dummy_responses = {
        "case_manager": "Case analysis complete. Accused: John Doe, Victim: Jane Smith, Offence: Theft.",
        "legal_research": "Applicable sections: IPC 378 (Theft), IPC 403 (Criminal misappropriation).",
        "prosecutor_r1": "Prosecution opening: The accused intentionally took the property.",
        "defense_r1": "Defense opening: Lack of intent and mistaken identity.",
        "prosecutor_r2": "Prosecution closing: Overwhelming evidence, guilty beyond doubt.",
        "defense_r2": "Defense closing: Reasonable doubt, acquittal required.",
        "judge": "Verdict: Guilty. Confidence: 85%. Reasoning: Evidence is substantial.",
        "reporter": "The court found the accused guilty. Sentenced to 3 years.",
        "consultant": "The case is strong for the prosecution.",
        "top_consultant": "Simulation realistic; verdict consistent."
    }
    return dummy_responses.get(agent_name, f"Dummy response for {agent_name}")

# ------------------------------------------------------------
# Core functions
# ------------------------------------------------------------
@observe(name="llm-prose-call", as_type="generation")
def call_claude(
    system: str,
    user: str,
    max_tokens: int = 1000,
    agent_name: str = None,
) -> str:
    """Call the selected LLM for a plain text response."""
    if MOCK_LLM:
        return _dummy_prose_response(agent_name)

    client, model = get_client_and_model(agent_name)
    if client is None:
        raise RuntimeError("LLM client not initialized")

    langfuse = get_client()
    langfuse.update_current_generation(model=model, metadata={"agent": agent_name, "provider": PROVIDER})

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return response.choices[0].message.content

@observe(name="llm-structured-call", as_type="generation")
def call_structured(
    system: str,
    user: str,
    schema: Type[T],
    agent_name: str = None,
    max_tokens: int = 2000,
) -> T:
    """Call the selected LLM for structured JSON output."""
    if MOCK_LLM:
        dummy_data = _dummy_structured_data(schema)
        return schema(**dummy_data)

    client, model = get_client_and_model(agent_name)
    if client is None:
        raise RuntimeError("LLM client not initialized")

    langfuse = get_client()
    langfuse.update_current_generation(model=model, metadata={"agent": agent_name, "provider": PROVIDER})

    # Build schema description
    pydantic_schema = schema.model_json_schema()
    schema_json = json.dumps(pydantic_schema, indent=2)

    system_with_schema = (
        f"{system}\n\n"
        f"You MUST respond with a single JSON object that exactly matches the schema below.\n"
        f"Return ONLY the JSON object, no other text, no markdown, no explanation.\n\n"
        f"Schema:\n{schema_json}"
    )

    extra_kwargs = {}
    if PROVIDER == "groq":
        extra_kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_with_schema},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=0.3,
        **extra_kwargs
    )

    response_text = response.choices[0].message.content

    # Clean up markdown fences if present
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    response_text = response_text.strip()

    try:
        response_json = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {e}\nResponse: {response_text}")

    return schema(**response_json)