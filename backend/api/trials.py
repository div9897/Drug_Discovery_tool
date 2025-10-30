import requests
from typing import List, Dict

BASE = "https://clinicaltrials.gov/api/query/study_fields"
FIELDS = [
    "NCTId",
    "BriefTitle",
    "Condition",
    "InterventionName",
    "InterventionType",
    "Phase",
    "OverallStatus",
    "StartDate",
    "CompletionDate",
]


def fetch_trials(drug: str, max_records: int = 20) -> List[Dict]:
    params = {
        "expr": drug,
        "fields": ",".join(FIELDS),
        "min_rnk": 1,
        "max_rnk": max_records,
        "fmt": "json",
    }
    try:
        r = requests.get(BASE, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        studies = data.get("StudyFieldsResponse", {}).get("StudyFields", [])
        results: List[Dict] = []
        for s in studies:
            results.append({
                "nct_id": (s.get("NCTId") or [""])[0],
                "title": (s.get("BriefTitle") or [""])[0],
                "conditions": s.get("Condition") or [],
                "interventions": s.get("InterventionName") or [],
                "intervention_types": s.get("InterventionType") or [],
                "phase": (s.get("Phase") or [""])[0],
                "status": (s.get("OverallStatus") or [""])[0],
                "start_date": (s.get("StartDate") or [""])[0],
                "completion_date": (s.get("CompletionDate") or [""])[0],
                "source_id": f"NCT:{(s.get('NCTId') or [''])[0]}"
            })
        return results
    except Exception:
        return []
