import requests
from typing import Dict, List, Tuple

def resolve_drug(drug_name: str) -> Dict:
    r = requests.get(
        "https://www.ebi.ac.uk/chembl/api/data/molecule/search.json",
        params={"q": drug_name}, timeout=25
    )
    r.raise_for_status()
    js = r.json()
    molecules = js.get("molecules", [])
    if not molecules:
        return {}
    m = molecules[0]
    return {
        "chembl_id": m.get("molecule_chembl_id"),
        "pref_name": m.get("pref_name") or drug_name,
        "synonyms": list({(m.get("pref_name") or drug_name), *[s.get("molecule_synonym") for s in (m.get("molecule_synonyms") or []) if s.get("molecule_synonym")]}),
        "smiles": (m.get("molecule_structures") or {}).get("canonical_smiles")
    }

def mechanism_and_targets(chembl_id: str) -> Tuple[str, List[str]]:
    if not chembl_id:
        return "", []
    r = requests.get(
        "https://www.ebi.ac.uk/chembl/api/data/mechanism.json",
        params={"molecule_chembl_id": chembl_id}, timeout=25
    )
    r.raise_for_status()
    mechs = r.json().get("mechanisms", [])
    if not mechs:
        return "", []
    mech = mechs[0]
    moa = mech.get("mechanism_of_action") or ""
    targets = []
    if mech.get("target_chembl_id"):
        targets.append(mech["target_chembl_id"])
    return moa, targets
