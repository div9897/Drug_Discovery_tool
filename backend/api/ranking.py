import math
from typing import Dict

PHASE_MAP = {
    "N/A": 0, "Early Phase 1": 1, "Phase 1": 1, "Phase 1/Phase 2": 1.5,
    "Phase 2": 2, "Phase 2/Phase 3": 2.5, "Phase 3": 3, "Phase 4": 4
}

def phase_to_num(phase_text: str) -> float:
    if not phase_text:
        return 0.0
    return PHASE_MAP.get(phase_text, 0.0)

def compute_score(features: Dict) -> float:
    """
    features:
      phase_max: float 0..4
      paper_count: int
      positive_outcome_hits: int
      target_overlap: float 0..1
      safety_penalty: float 0..2
      boxed_warning: bool
    """
    phase = features.get("phase_max", 0.0)
    papers = features.get("paper_count", 0)
    pos = features.get("positive_outcome_hits", 0)
    overlap = features.get("target_overlap", 0.0)
    safety_penalty = features.get("safety_penalty", 0.0)
    boxed = 1.0 if features.get("boxed_warning", False) else 0.0

    score = (
        1.8 * phase
        + 0.6 * math.log1p(max(papers, pos))  # small boost for more supportive text
        + 1.2 * overlap
        - 0.9 * safety_penalty
        - 1.5 * boxed
    )
    return round(float(score), 3)
