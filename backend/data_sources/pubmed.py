from typing import List, Dict

from services.epmc import search_papers


def fetch_pubmed_abstracts(query: str, retmax: int = 15) -> List[Dict]:
    # Reuse existing EuropePMC wrapper for literature
    _, papers = search_papers(query, query)
    results = []
    for p in papers[:retmax]:
        results.append({
            "type": "literature",
            "source": "europe_pmc",
            "source_id": p.get("pmid"),
            "title": p.get("title"),
            "snippet": p.get("snippet"),
            "year": p.get("year"),
            "url": p.get("url"),
        })
    return results


