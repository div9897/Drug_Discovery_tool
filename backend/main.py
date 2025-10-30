# backend/main.py
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Tuple
import os, time, concurrent.futures as cf, traceback

from dotenv import load_dotenv
import requests_cache

from models import SearchResponse, SearchFilters, Candidate, EvidenceItem, SafetyInfo
from services.epmc import search_papers
from services.ctgov import search_trials_by_disease
from services.chembl import resolve_drug, mechanism_and_targets
from services.openfda import label_info
from ranking import compute_score

load_dotenv()
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "")
ALLOWED = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501").split(",")

# ---- performance knobs ----
CANDIDATE_LIMIT = 5
PAPERS_PER_DRUG = 8
THREADS = 8
OVERALL_DEADLINE = 35.0  # sec

# Cache HTTP for 6h; return stale on upstream error
requests_cache.install_cache("ps11_cache", expire_after=6*60*60, stale_if_error=True)

app = FastAPI(title="PS11 Drug Repurposing API", version="0.4")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryBody(BaseModel):
    disease: str
    filters: SearchFilters = SearchFilters()

SAFE_FALLBACK_DRUGS = ["Metformin", "Atorvastatin", "Aspirin", "Doxycycline"]

@app.get("/health")
def health():
    return {"ok": True, "version": "0.4"}

def mock_candidates(disease: str) -> List[Candidate]:
    """Safe-mode mock for demo; no external calls."""
    base = [
        ("Metformin", 2.0, "AMPK activation may confer benefits in metabolic & neurodegenerative pathways."),
        ("Atorvastatin", 3.0, "Anti-inflammatory and lipid-lowering effects with pleiotropic pathways."),
        ("Doxycycline", 2.0, "MMP inhibition and anti-inflammatory properties suggest repurposing potential.")
    ]
    res: List[Candidate] = []
    for i, (drug, phase, moa) in enumerate(base, start=1):
        res.append(Candidate(
            rank=i,
            drug=drug,
            synonyms=[],
            ids={"chembl": ""},
            mechanism=moa,
            score=compute_score({
                "phase_max": phase, "paper_count": 5, "positive_outcome_hits": 2,
                "target_overlap": 0.5, "safety_penalty": 0.0, "boxed_warning": False
            }),
            kpis={"best_trial_phase": phase, "papers": 5, "pos_outcome_snippets": 2},
            safety=SafetyInfo(boxed_warning=False, highlights=[]),
            evidence=[EvidenceItem(type="paper", id="PMID:demo", title=f"{drug} and {disease}",
                                   snippet="Demo evidence (safe mode).", url=None, source="mock")]
        ))
    res.sort(key=lambda c: c.score, reverse=True)
    for i, c in enumerate(res, start=1): c.rank = i
    return res

def build_candidate(disease: str, drug: str, phase_num: float, trials_for_drug: list) -> Candidate:
    # (a) EuropePMC
    pos_hits, papers = search_papers(disease, drug, email=CONTACT_EMAIL)
    papers = papers[:PAPERS_PER_DRUG]
    # (b) ChEMBL
    chem = resolve_drug(drug)
    moa, targets = mechanism_and_targets(chem.get("chembl_id"))
    # (c) openFDA
    pref = chem.get("pref_name") or drug
    safety_js = label_info(pref.upper())
    safety = SafetyInfo(
        boxed_warning=bool(safety_js.get("boxed_warning")),
        highlights=(safety_js.get("highlights", [])[:2] if isinstance(safety_js.get("highlights", []), list) else [])
    )
    # (d) Features & score
    features = {
        "phase_max": phase_num,
        "paper_count": len(papers),
        "positive_outcome_hits": pos_hits,
        "target_overlap": 1.0 if targets else 0.0,
        "safety_penalty": 1.0 if safety.boxed_warning else 0.2 * len(safety.highlights),
        "boxed_warning": safety.boxed_warning
    }
    score = compute_score(features)
    # (e) Evidence
    evidence: List[EvidenceItem] = []
    for p in papers[:3]:
        evidence.append(EvidenceItem(
            type="paper", id=f"PMID:{p.get('pmid')}", title=p.get("title"),
            snippet=p.get("snippet"), year=p.get("year"), url=p.get("url"), source="europe_pmc"
        ))
    if moa:
        evidence.append(EvidenceItem(
            type="moa", id=chem.get("chembl_id") or "", title="Mechanism of Action",
            snippet=str(moa)[:300],
            url=f"https://www.ebi.ac.uk/chembl/compound_report_card/{chem.get('chembl_id')}/" if chem.get("chembl_id") else None,
            source="chembl"
        ))

    # add 1–2 trial snippets for THIS drug
    for t in (trials_for_drug or [])[:2]:
        evidence.append(EvidenceItem(
            type="trial",
            id=f"NCT:{t.get('nct_id')}",
            title="Primary outcome",
            snippet=t.get("snippet"),
            url=t.get("url"),
            source="clinicaltrials"
        ))

    return Candidate(
        rank=0, drug=pref, synonyms=chem.get("synonyms", []), ids={"chembl": chem.get("chembl_id") or ""},
        mechanism=moa or None, score=score,
        kpis={"best_trial_phase": features["phase_max"], "papers": len(papers), "pos_outcome_snippets": pos_hits},
        safety=safety, evidence=evidence
    )

@app.post("/search", response_model=SearchResponse)
def search(q: QueryBody, safe: int = Query(0, description="Safe-mode: 1 returns mock results instantly")):
    start = time.monotonic()
    disease = q.disease.strip()
    filt = q.filters

    # SAFE MODE: immediate mock data for demos / debugging
    if safe == 1:
        return SearchResponse(query=disease, disease_canonical=disease, filters_applied=filt, results=mock_candidates(disease))

    try:
        # 1) Per-drug phases from trials (fast)
        drug_phase, trials_by_drug, _seen_trials = search_trials_by_disease(disease)
        if not drug_phase:
    # No interventions found for this condition — return empty so the UI shows the warning
            return SearchResponse(query=disease, disease_canonical=disease, filters_applied=filt, results=[])


        # 2) Top N by phase
        items: List[Tuple[str, float]] = sorted(
            drug_phase.items(), key=lambda kv: (-kv[1], kv[0].lower())
        )[:CANDIDATE_LIMIT]

        # 3) Build in parallel within deadline
        results: List[Candidate] = []
        remaining = OVERALL_DEADLINE - (time.monotonic() - start)
        if remaining <= 0:
            return SearchResponse(query=disease, disease_canonical=disease, filters_applied=filt, results=[])
        items = sorted(drug_phase.items(), key=lambda kv: (-kv[1], kv[0].lower()))[:CANDIDATE_LIMIT]
        with cf.ThreadPoolExecutor(max_workers=THREADS) as pool:
            futs = {pool.submit(build_candidate, disease, drug, ph, trials_by_drug.get(drug, [])): (drug, ph) for drug, ph in items}
            done, not_done = cf.wait(futs.keys(), timeout=remaining)
            for fut in done:
                try:
                    results.append(fut.result())
                except Exception as e:
                    print("CANDIDATE ERROR:", e, traceback.format_exc())
            for fut in not_done:
                fut.cancel()

        # 4) Filters & rank
        filtered: List[Candidate] = []
        for c in results:
            if filt.min_phase and (c.kpis.get("best_trial_phase", 0.0) < float(filt.min_phase)):
                continue
            if filt.exclude_boxed_warnings and c.safety.boxed_warning:
                continue
            filtered.append(c)
        filtered.sort(key=lambda c: c.score, reverse=True)
        for i, c in enumerate(filtered, start=1):
            c.rank = i

        return SearchResponse(query=disease, disease_canonical=disease, filters_applied=filt, results=filtered[:CANDIDATE_LIMIT])

    except Exception as e:
        # Never crash the socket; return structured error with empty results
        print("SEARCH FATAL:", e, traceback.format_exc())
        return SearchResponse(query=disease, disease_canonical=disease, filters_applied=filt, results=[])
    
from typing import List
# (imports above already exist)

@app.post("/search_fast", response_model=SearchResponse)
def search_fast(q: QueryBody):
    """
    Ultra-stable endpoint: uses only ClinicalTrials.gov to propose drugs by intervention & phase.
    No external literature/chem/safety calls => no crashes/timeouts.
    """
    disease = q.disease.strip()
    filt = q.filters

    # pull interventions & phases
    drug_phase, trials_by_drug, _ = search_trials_by_disease(disease)
    results: List[Candidate] = []

    # build minimal candidates (phase + few trials only)
    for drug, ph in sorted(drug_phase.items(), key=lambda kv: (-kv[1], kv[0].lower()))[:10]:
        # filters
        if filt.min_phase and ph < float(filt.min_phase):
            continue

        ev = []
        for t in (trials_by_drug.get(drug) or [])[:2]:
            ev.append(EvidenceItem(
                type="trial",
                id=f"NCT:{t.get('nct_id')}",
                title="Primary outcome",
                snippet=t.get("snippet"),
                url=t.get("url"),
                source="clinicaltrials"
            ))

        c = Candidate(
            rank=0,
            drug=drug,
            synonyms=[],
            ids={"chembl": ""},
            mechanism=None,
            score=ph + 0.1 * len(ev),  # simple score: phase + a tiny bump for evidence items
            kpis={"best_trial_phase": ph, "papers": 0, "pos_outcome_snippets": 0},
            safety=SafetyInfo(boxed_warning=False, highlights=[]),
            evidence=ev
        )
        results.append(c)

    results.sort(key=lambda c: c.score, reverse=True)
    for i, c in enumerate(results, start=1):
        c.rank = i

    return SearchResponse(
        query=disease,
        disease_canonical=disease,
        filters_applied=filt,
        results=results
    )
