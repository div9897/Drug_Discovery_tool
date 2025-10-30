# Drug Discovery & Repurposing Assistant

This is a proof-of-concept web application that helps researchers discover and repurpose drugs for a given disease or condition. It leverages public APIs to gather data from various sources, including ClinicalTrials.gov, ChEMBL, Europe PMC, and openFDA.

## Features

*   *Disease-based Search:* Search for drugs and interventions related to a specific disease or condition.
*   *Data Aggregation:* Gathers and displays data from multiple sources in a unified interface.
*   *Drug Ranking:* Ranks potential drug candidates based on a scoring algorithm.
*   *Evidence Exploration:* Provides evidence and supporting data for each drug candidate.
*   *Filtering:* Allows users to filter results based on trial phase, safety warnings, and more.

## Technologies Used

*   *Backend:*
    *   [FastAPI](https://fastapi.tiangolo.com/): A modern, fast (high-performance) web framework for building APIs with Python 3.7+.
    *   [uvicorn](https://www.uvicorn.org/): An ASGI server for running FastAPI applications.
    *   [requests](https://requests.readthedocs.io/en/latest/): A simple, yet elegant HTTP library for Python.
    *   [requests-cache](https://requests-cache.readthedocs.io/en/latest/): A persistent cache for the requests library.
*   *Frontend:*
    *   [Streamlit](https://streamlit.io/): A faster way to build and share data apps.
    *   [pandas](https://pandas.pydata.org/): A fast, powerful, flexible, and easy-to-use open-source data analysis and manipulation tool.

## Setup

1.  *Clone the repository:*
    bash
    git clone <repository-url>
    cd <repository-directory>
    
2.  *Install backend dependencies:*
    bash
    pip install -r backend/requirements.txt
    
3.  *Install frontend dependencies:*
    bash
    pip install -r frontend/requirement.txt
    

## Usage

1.  *Start the backend server:*
    bash
    cd backend
    uvicorn main:app --host 0.0.0.0 --port 8000
    
2.  *Start the frontend server:*
    bash
    streamlit run frontend/app.py
    
3.  *Open the application in your browser:*
    Navigate to the URL provided by Streamlit (usually http://localhost:8501).

## Known Issues

*   *Backend Stability:* The /search endpoint is prone to segmentation faults when running with concurrent requests. The root cause appears to be related to the ThreadPoolExecutor, but further investigation is needed. As a temporary workaround, the concurrent execution has been disabled in the search function in backend/main.py.
*   *Frontend Performance:* The frontend application can be slow to load, especially when querying the /search endpoint. This is due to the sequential nature of the backend processing.
*   *UI Hangs:* The frontend may hang or become unresponsive, especially on the initial load. The cause is under investigation but is likely related to the backend performance issues.
