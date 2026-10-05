"""Org3 Platform REST API — Multi-Tenant Organizational Operating System & Governance Protocol.

Versione: 3.3.0 (Sequenza 5 — Step 5.2)
Target: Cloud Run / FastAPI (org3.godigix.com -> org3.ai)
"""

from __future__ import annotations

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from org3.api.routers import approvals, delegation, members, organizations, storage, tokens

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

app = FastAPI(
    title="Org3 Platform API",
    description="Multi-Tenant Organizational Operating System, IAM, and Delegation Protocol for the AI Era.",
    version="3.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Policy aperta per client Web e connettori autorizzati
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusione dei Router
app.include_router(organizations.router)
app.include_router(members.router)
app.include_router(delegation.router)
app.include_router(approvals.router)
app.include_router(tokens.router)
app.include_router(storage.router)


@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint per Cloud Run e monitoring."""
    return {
        "status": "healthy",
        "service": "org3-platform-api",
        "version": "3.3.0",
        "protocol": "Org3 Multi-Tenant Governance",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("org3.api.main:app", host="0.0.0.0", port=8005, reload=True)
