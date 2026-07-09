from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class EvaluationMetrics:
    overall_quality_score: float
    completeness: float
    coherence: float
    legal_accuracy: float
    node_times: Dict[str, float]

class SystemEvaluator:
    """Simple evaluator for courtroom simulation cases."""
    
    def evaluate_case(self, case_state: Dict[str, Any], node_times: Dict[str, float]) -> EvaluationMetrics:
        """
        Evaluate a completed simulation.
        Returns an EvaluationMetrics object.
        """
        # Compute completeness: how many of the expected fields are filled?
        expected_fields = [
            "case_intake", "legal_research", "consultant", "top_consultant",
            "pros_r1", "def_r1", "pros_r2", "def_r2",
            "judge_verdict", "headline", "report"
        ]
        filled = sum(1 for f in expected_fields if case_state.get(f) is not None and case_state.get(f) != "")
        completeness = filled / len(expected_fields) * 100

        # Coherence: simple heuristic – if judge verdict exists and report exists, high coherence
        coherence = 80.0
        if case_state.get("judge_verdict") and case_state.get("report"):
            coherence = 90.0
        elif case_state.get("judge_verdict") or case_state.get("report"):
            coherence = 60.0
        else:
            coherence = 30.0

        # Legal accuracy: dummy – we can make it depend on whether sections_applied exists
        legal_accuracy = 70.0
        if case_state.get("judge_verdict"):
            jv = case_state["judge_verdict"]
            if isinstance(jv, dict) and jv.get("sections_applied"):
                legal_accuracy = 85.0

        # Overall quality: weighted average
        overall = (completeness * 0.4 + coherence * 0.3 + legal_accuracy * 0.3)

        return EvaluationMetrics(
            overall_quality_score=overall,
            completeness=completeness,
            coherence=coherence,
            legal_accuracy=legal_accuracy,
            node_times=node_times
        )