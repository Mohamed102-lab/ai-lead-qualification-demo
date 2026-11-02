"""HTTP wrapper around the rules, called by the n8n workflow."""

from __future__ import annotations

import os

from fastapi import FastAPI, Header, HTTPException

from .rules import load_rules, score_lead

app = FastAPI(title="Lead scoring service")
API_KEY = os.environ.get("SCORING_API_KEY", "")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/score")
def score(lead: dict, x_api_key: str = Header(default="")) -> dict:
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    # Rules are re-read on every call, so edits to rules.json apply without a restart.
    result = score_lead(lead, load_rules())
    return {"booking_id": lead.get("booking_id"), **result.to_dict()}
