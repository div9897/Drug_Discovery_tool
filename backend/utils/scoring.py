from typing import List, Dict


def score_opportunity(drug: str, disease: str, evidence: List[Dict]) -> float:
    trials = [e for e in evidence if e.get("type") == "trial"]
    pubs = [e for e in evidence if e.get("type") == "literature"]
    return min(1.0, 0.05 * len(trials) + 0.02 * len(pubs))


