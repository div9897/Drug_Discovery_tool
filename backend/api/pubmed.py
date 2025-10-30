import requests
from typing import List, Dict

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def fetch_pubmed_abstracts(drug: str, retmax: int = 10) -> List[Dict]:
    params = {"db": "pubmed", "term": drug, "retmode": "json", "retmax": retmax}
    try:
        ids_resp = requests.get(ESEARCH, params=params, timeout=20)
        ids_resp.raise_for_status()
        idlist = ids_resp.json().get("esearchresult", {}).get("idlist", [])
        if not idlist:
            return []
        ids = ",".join(idlist)
        fetch_params = {"db": "pubmed", "id": ids, "retmode": "xml"}
        data = requests.get(EFETCH, params=fetch_params, timeout=30)
        data.raise_for_status()
        # Simple XML parsing by string ops to keep dependencies low
        xml = data.text
        results: List[Dict] = []
        for pmid in idlist:
            # Extract title
            title_tag = f"<ArticleId IdType=\"pubmed\">{pmid}</ArticleId>"
            idx = xml.find(title_tag)
            if idx == -1:
                continue
            # Backtrack to ArticleTitle and AbstractText nearest before this id occurrence
            at_start = xml.rfind("<ArticleTitle>", 0, idx)
            at_end = xml.find("</ArticleTitle>", at_start)
            title = xml[at_start + 14:at_end] if at_start != -1 and at_end != -1 else ""
            ab_start = xml.rfind("<Abstract>", 0, idx)
            ab_end = xml.find("</Abstract>", ab_start)
            abstract = xml[ab_start:ab_end] if ab_start != -1 and ab_end != -1 else ""
            # Strip tags from abstract
            abstract = abstract.replace("<Abstract>", "").replace("</Abstract>", "")
            abstract = abstract.replace("<AbstractText>", "").replace("</AbstractText>", "")
            results.append({
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "source_id": f"PMID:{pmid}"
            })
        return results
    except Exception:
        return []
