from typing import List, Dict


def summarize_evidence(drug: str, disease: str, evidence: List[Dict]) -> str:
    trials = [e for e in evidence if e.get("type") == "trial"]
    pubs = [e for e in evidence if e.get("type") == "literature"]
    return f"Evidence for {drug} in {disease}: {len(trials)} trials and {len(pubs)} publications."


