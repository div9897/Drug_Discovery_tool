import requests
from collections import defaultdict
from typing import Dict, List, Tuple
from ranking import phase_to_num

# Robust parser for ClinicalTrials.gov v2
# Returns:
#   - drug_phase: dict[str, float] (best phase number per drug)
#   - trials_by_drug: dict[str, list[dict]] (a few trials per drug for evidence)
#   - seen_trials: flat list of simplified trial dicts (optional use)
PHASE_MAP = {
    "N/A": 0.0, "EARLY PHASE 1": 1.0, "PHASE 1": 1.0, "PHASE 1/PHASE 2": 1.5,
    "PHASE 2": 2.0, "PHASE 2/PHASE 3": 2.5, "PHASE 3": 3.0, "PHASE 4": 4.0
}

def _phase_to_num(phases: List[str]) -> float:
    if not phases:
        return 0.0
    # take the most advanced phase mentioned
    best = 0.0
    for p in phases:
        v = PHASE_MAP.get(p.strip().upper(), 0.0)
        if v > best:
            best = v
    return best

def _clean_intervention_name(name: str) -> str:
    # CTGOV frequently prefixes like "Drug: Metformin" or "Biological: X"
    if not name:
        return ""
    parts = name.split(":", 1)
    return parts[1].strip() if len(parts) == 2 else name.strip()

def search_trials_by_disease(disease: str, size: int = 200) -> Tuple[Dict[str, float], Dict[str, List[dict]], List[dict]]:
    params = {"format": "json", "query.cond": disease, "pageSize": size}
    r = requests.get("https://clinicaltrials.gov/api/v2/studies", params=params, timeout=25)
    r.raise_for_status()
    data = r.json()
    studies = data.get("studies", [])

    drug_phase: Dict[str, float] = defaultdict(float)
    trials_by_drug: Dict[str, List[dict]] = defaultdict(list)
    seen_trials: List[dict] = []

    for s in studies:
        psec = s.get("protocolSection", {})
        idm = psec.get("identificationModule", {})
        nct = idm.get("nctId")
        conds = (psec.get("conditionsModule", {}) or {}).get("conditions", []) or []
        phases = (psec.get("designModule", {}) or {}).get("phases", []) or []
        phase_num = _phase_to_num(phases)
        status = (psec.get("statusModule", {}) or {}).get("overallStatus")
        outcomes = (psec.get("outcomesModule", {}) or {}).get("primaryOutcomes", []) or []
        snippet = None
        if outcomes:
            measure = outcomes[0].get("measure") or ""
            desc = outcomes[0].get("description") or ""
            snippet = f"{measure} {desc}".strip()[:400] or None

        # interventions can be under armsInterventionsModule.interventions
        # or appear in design/outcomes blocks; handle typical path
        intervs = (psec.get("armsInterventionsModule", {}) or {}).get("interventions", []) or []
        names = []
        for it in intervs:
            nm = it.get("name") or ""
            if nm:
                names.append(_clean_intervention_name(nm))

        trial_row = {
            "nct_id": nct,
            "conditions": conds,
            "phases": phases,
            "phase_num": phase_num,
            "status": status,
            "snippet": snippet,
            "url": f"https://clinicaltrials.gov/study/{nct}" if nct else None,
            "interventions": names
        }
        seen_trials.append(trial_row)

        for dn in names:
            if not dn:
                continue
            # keep best phase per drug
            if phase_num > drug_phase[dn]:
                drug_phase[dn] = phase_num
            # store up to a few trials as evidence
            if len(trials_by_drug[dn]) < 3:
                trials_by_drug[dn].append(trial_row)

    return dict(drug_phase), dict(trials_by_drug), seen_trials
