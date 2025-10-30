from typing import Dict

from services.chembl import resolve_drug, mechanism_and_targets
from services.openfda import label_info


def fetch_drug_info(name: str) -> Dict:
    chem = resolve_drug(name)
    moa, targets = mechanism_and_targets(chem.get("chembl_id"))
    pref = chem.get("pref_name") or name
    safety_js = label_info(pref.upper())
    return {
        "name": pref,
        "chembl_id": chem.get("chembl_id"),
        "synonyms": chem.get("synonyms", []),
        "mechanism": moa,
        "targets": targets,
        "safety": {
            "boxed_warning": bool(safety_js.get("boxed_warning")),
            "highlights": safety_js.get("highlights", []) if isinstance(safety_js.get("highlights", []), list) else [],
        },
    }


