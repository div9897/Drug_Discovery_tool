# Drug Repurposing Assistant  
**Team Name:** *VIBE*
**Team ID:** *TEAM135*
**Team Members:**  
- Divyanshu Saini  
- Divyansh Sharma  
- Divam Sharma  
- Vishakha Singh  

---

## Table of Contents
- [Features](#features)
- [Architecture](#architecture)
- [Directory Structure](#directory-structure)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Running Services Separately](#running-services-separately)
- [Configuration](#configuration)
- [Frontend Usage](#frontend-usage)
- [Backend API](#backend-api)
- [Theming](#theming)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [License](#license)

---

## Features

- **Treatments discovery** (condition → candidate medicines)  
  - Filters: minimum trial phase, minimum year  
  - Evidence-aware cards with Trials/Pubs/Top phase, sources and CSV export  

- **Molecule Explorer** (condition → interactive grid)  
  - Confidence bar chart; card metrics (Trials, Pubs, Top)  
  - Market/Patent/Regulatory summaries with normalized scores (0–100)  

- **Drug Comparison Mode**  
  - Pick two drugs, see side-by-side Trials, Publications, Boxed warning, Mechanism  
  - “Why this drug?” rationale and theoretical head-to-head score  
  - Interactive charts (Plotly) with a Streamlit fallback  

- **Professional Theme:** *NeoBio Intelligence*  

---

## Architecture

- **Backend:** FastAPI (Python). Aggregates public sources (EuropePMC, ClinicalTrials.gov, ChEMBL, openFDA) through a thin `data_sources` layer and exposes REST endpoints.  
- **Frontend:** Streamlit (Python). Calls backend APIs directly and renders interactive dashboards.  

**Data Flow:**  
1. User enters a condition or drug on the frontend.  
2. Frontend calls FastAPI endpoints (`/api/treat`, `/api/explorer`, `/api/drug/{name}`, `/api/literature`, `/api/trials`).  
3. Backend fetches and normalizes responses from data sources, combines and scores evidence.  
4. Frontend renders cards, tables, and charts, with options for export and comparison.  

---
