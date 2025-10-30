from typing import Dict, List


def extract_diseases(abstracts: List[dict], trials: List[dict]) -> Dict[str, List[dict]]:
    # Minimal heuristic: group all evidence under a single placeholder disease if any mention exists
    bucket: Dict[str, List[dict]] = {}
    for ev in abstracts + trials:
        disease = ev.get("disease") or ev.get("condition") or "General"
        bucket.setdefault(disease, []).append(ev)
    return bucket


def extract_drugs(abstracts: List[dict], trials: List[dict]) -> Dict[str, List[dict]]:
    # Minimal heuristic: use intervention names from trials as medicines
    bucket: Dict[str, List[dict]] = {}
    for t in trials:
        for iv in t.get("interventions", []) or []:
            name = iv if isinstance(iv, str) else iv.get("name")
            if not name:
                continue
            bucket.setdefault(name, []).append(t)
    # If nothing from trials, fall back to a single medicine from abstracts
    if not bucket and abstracts:
        bucket.setdefault("Unknown", []).extend(abstracts)
    return bucket


