import requests
from typing import Dict, List

def label_info(drug_name: str) -> Dict:
    """
    Returns boxed warning flag and highlights (if any)
    """
    try:
        r = requests.get(
            "https://api.fda.gov/drug/label.json",
            params={"search": f'openfda.brand_name:("{drug_name}")', "limit": 3},
            timeout=25
        )
        if r.status_code != 200:
            return {"boxed_warning": False, "highlights": []}
        res = r.json().get("results", [])
        if not res:
            return {"boxed_warning": False, "highlights": []}
        boxed_texts = []
        for it in res:
            if "boxed_warning" in it:
                boxed_texts.append(it["boxed_warning"][0][:300])
        return {
            "boxed_warning": len(boxed_texts) > 0,
            "highlights": boxed_texts[:2]
        }
    except Exception:
        return {"boxed_warning": False, "highlights": []}
