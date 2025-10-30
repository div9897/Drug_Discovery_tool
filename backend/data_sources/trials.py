from typing import List, Dict

from services.ctgov import search_trials_by_disease


def fetch_trials(query: str, max_records: int = 20) -> List[Dict]:
    drug_phase, trials_by_drug, all_trials = search_trials_by_disease(query)
    # Flatten minimal schema for routes consumers
    results: List[Dict] = []
    for t in all_trials[:max_records]:
        # derive a simple phase label for convenience
        phases = t.get("phases", []) or []
        phase_label = ""
        ranks = {"PHASE 3": 3, "PHASE 2": 2, "PHASE 1": 1, "EARLY PHASE 1": 1, "PHASE 4": 4, "N/A": 0}
        best_rank = -1
        for p in phases:
            r = ranks.get((p or "").strip().upper(), 0)
            if r > best_rank:
                best_rank = r
                phase_label = p
        results.append({
            "type": "trial",
            "source": "clinicaltrials",
            "source_id": t.get("nct_id"),
            "title": t.get("title") or t.get("primary_outcome"),
            "snippet": t.get("snippet") or t.get("primary_outcome"),
            "phase": phase_label,
            "start_date": t.get("start_date"),
            "completion_date": t.get("completion_date"),
            "url": t.get("url"),
            "interventions": t.get("interventions", []),
        })
    return results


