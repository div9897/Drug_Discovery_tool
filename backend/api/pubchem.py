import requests
from typing import Dict, Optional

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


def fetch_drug_info(name: str) -> Optional[Dict]:
    try:
        # Get CID
        r = requests.get(f"{BASE}/compound/name/{name}/cids/JSON", timeout=20)
        if r.status_code != 200:
            return None
        cids = r.json().get("IdentifierList", {}).get("CID", [])
        if not cids:
            return None
        cid = cids[0]
        # Get summary
        s = requests.get(f"{BASE}/compound/cid/{cid}/JSON", timeout=20)
        s.raise_for_status()
        data = s.json()
        props = data.get("PC_Compounds", [{}])[0]
        return {"cid": cid, "raw": props}
    except Exception:
        return None
