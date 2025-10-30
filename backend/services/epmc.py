import requests, re
from typing import List, Dict, Tuple

POSITIVE_CUES = [
    r"\bimprov(ed|ement)\b", r"\bsignificant(ly)?\b", r"\befficac(y|ious)\b",
    r"\breduc(e|ed|tion)\b", r"\bbenefit(ed)?\b", r"\bresponse\b", r"\bremission\b"
]

def search_papers(disease: str, drug: str, size: int = 20, email: str = "") -> Tuple[int, List[Dict]]:
    query = f'({drug}) AND ({disease})'
    params = {"query": query, "resultType": "core", "pageSize": size, "format": "json"}
    headers = {"User-Agent": f"ps11-hackathon ({email})"} if email else {}
    r = requests.get("https://www.ebi.ac.uk/europepmc/webservices/rest/search", params=params, headers=headers, timeout=25)
    r.raise_for_status()
    data = r.json()
    items = data.get("resultList", {}).get("result", [])
    positive_hits = 0
    papers = []
    for it in items:
        abs_text = it.get("abstractText", "") or ""
        if any(re.search(p, abs_text, flags=re.I) for p in POSITIVE_CUES):
            positive_hits += 1
        papers.append({
            "pmid": it.get("pmid") or it.get("id"),
            "title": it.get("title"),
            "year": int(it.get("pubYear")) if it.get("pubYear") and it.get("pubYear").isdigit() else None,
            "url": f'https://europepmc.org/abstract/MED/{it.get("pmid")}' if it.get("pmid") else None,
            "snippet": abs_text[:400]
        })
    return positive_hits, papers
