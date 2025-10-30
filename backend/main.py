from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from api.routes import router as api_router


ALLOWED = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501").split(",")

app = FastAPI(title="Drug Repurposing API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


# New modular API mounted under /api
app.include_router(api_router, prefix="/api")


