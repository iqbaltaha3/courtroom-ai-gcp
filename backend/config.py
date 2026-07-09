"""
Simple configuration for the Courtroom AI backend.

Single provider: Groq. One model is used for every agent by default,
but you can still override the model per-agent in config.yaml if you want.
"""

import os
import yaml
from dataclasses import dataclass
from typing import Literal, Dict
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


@dataclass
class AgentConfig:
    """Per-agent configuration."""
    name: str
    model: str
    call_type: Literal["prose", "structured"] = "prose"
    max_tokens: int = 1000


class Config:
    """Loads agent configuration from config.yaml (Groq-only)."""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or str(Path(__file__).parent / "config.yaml")
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.yaml_data = self._load_yaml()
        self.agent_configs = self._build_agent_configs()

    def _load_yaml(self) -> dict:
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")
        with open(config_file, "r") as f:
            return yaml.safe_load(f) or {}

    def _build_agent_configs(self) -> Dict[str, AgentConfig]:
        agents_data = self.yaml_data.get("agents", {})
        agent_configs = {}
        for agent_name, agent_data in agents_data.items():
            agent_configs[agent_name] = AgentConfig(
                name=agent_name,
                model=agent_data.get("model", DEFAULT_MODEL),
                call_type=agent_data.get("call_type", "prose"),
                max_tokens=agent_data.get("max_tokens", 1000),
            )
        return agent_configs

    def get_agent_config(self, agent_name: str) -> AgentConfig:
        if agent_name not in self.agent_configs:
            # Fall back to the default model instead of hard failing —
            # keeps things simple if an agent is missing from config.yaml.
            return AgentConfig(name=agent_name, model=DEFAULT_MODEL)
        return self.agent_configs[agent_name]

    def get_model(self, agent_name: str) -> str:
        return self.get_agent_config(agent_name).model

    def validate_setup(self) -> tuple[bool, str]:
        if not self.groq_api_key:
            return False, "No GROQ_API_KEY set. Add it to your .env file."
        return True, "✓ Groq API key configured"


# Global config instance
config = Config()
