"""FastAPI entrypoint for backend API routes."""

from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI

from backend.api import debate, disruptions, news_curator, resolution_prep, supply_chain

# Load local .env automatically for development.
load_dotenv()

app = FastAPI(
    title="Supply Chain Resilience API",
    version="0.1.0",
    description="Backend for the Singapore Supply Chain Resilience Management System",
)

API_PREFIX = "/api/v1"

app.include_router(supply_chain.router, prefix=API_PREFIX)
app.include_router(news_curator.router, prefix=API_PREFIX)
app.include_router(disruptions.router, prefix=API_PREFIX)
app.include_router(resolution_prep.router, prefix=API_PREFIX)
app.include_router(debate.router, prefix=API_PREFIX)
