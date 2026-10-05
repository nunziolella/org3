"""Router for Human-in-the-Loop (HITL) Approvals and Notification Hub in Org3 Platform."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from org3.api.db import get_db
from org3.models.multitenant import ApprovalRequest, ApprovalStatus

router = APIRouter(prefix="/v1/approvals", tags=["Approvals & HITL Hub"])


class SubmitApprovalRequest(BaseModel):
    org_id: str
    source_service: str = Field(default="structura", max_length=64)
    risk_class: str = Field(default="C", max_length=8)
    title: str = Field(..., max_length=255)
    description: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    requested_by: Optional[str] = None


class ResolveApprovalRequest(BaseModel):
    action: str = Field(..., description="'APPROVED' oppure 'REJECTED'")
    resolution_note: Optional[str] = None
    resolved_by: Optional[str] = None


@router.post("/request", response_model=ApprovalRequest, status_code=status.HTTP_201_CREATED)
def submit_approval_request(req: SubmitApprovalRequest, db=Depends(get_db)):
    """Invia una nuova richiesta di autorizzazione umana (HITL) al centro notifiche di Org3."""
    cur = db.cursor()
    cur.execute("SELECT id FROM org3_organizations WHERE id = %s;", (req.org_id,))
    if not cur.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizzazione non trovata.")

    cur.execute(
        """
        INSERT INTO org3_approval_requests (org_id, source_service, risk_class, title, description, payload, requested_by, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'PENDING')
        RETURNING id, org_id, source_service, risk_class, title, description, payload, requested_by, status, resolution_note, resolved_by, resolved_at, created_at;
    """,
        (
            req.org_id,
            req.source_service,
            req.risk_class.upper(),
            req.title.strip(),
            req.description.strip(),
            json.dumps(req.payload),
            req.requested_by,
        ),
    )
    row = cur.fetchone()
    return ApprovalRequest(**dict(row))


@router.get("", response_model=List[ApprovalRequest])
def list_approval_requests(
    org_id: str,
    status_filter: Optional[ApprovalStatus] = None,
    risk_class: Optional[str] = None,
    db=Depends(get_db),
):
    """Elenca le richieste di approvazione per un'organizzazione."""
    cur = db.cursor()
    query = """
        SELECT id, org_id, source_service, risk_class, title, description, payload, requested_by, status, resolution_note, resolved_by, resolved_at, created_at
        FROM org3_approval_requests
        WHERE org_id = %s
    """
    params = [org_id]
    if status_filter is not None:
        query += " AND status = %s"
        params.append(status_filter.value)
    if risk_class is not None:
        query += " AND risk_class = %s"
        params.append(risk_class.upper())
    query += " ORDER BY created_at DESC;"

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    return [ApprovalRequest(**dict(r)) for r in rows]


@router.get("/{approval_id}", response_model=ApprovalRequest)
def get_approval_request(approval_id: str, db=Depends(get_db)):
    """Recupera il dettaglio di una richiesta di approvazione."""
    cur = db.cursor()
    cur.execute(
        """
        SELECT id, org_id, source_service, risk_class, title, description, payload, requested_by, status, resolution_note, resolved_by, resolved_at, created_at
        FROM org3_approval_requests
        WHERE id = %s;
    """,
        (approval_id,),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Richiesta di approvazione non trovata.")
    return ApprovalRequest(**dict(row))


@router.post("/{approval_id}/resolve", response_model=ApprovalRequest)
def resolve_approval_request(approval_id: str, req: ResolveApprovalRequest, db=Depends(get_db)):
    """Approva o Rifiuta una richiesta Human-in-the-Loop."""
    action = req.action.strip().upper()
    if action not in ["APPROVED", "REJECTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Azione non valida: specificare 'APPROVED' o 'REJECTED'."
        )

    cur = db.cursor()
    cur.execute("SELECT id, status FROM org3_approval_requests WHERE id = %s;", (approval_id,))
    existing = cur.fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Richiesta di approvazione non trovata.")

    if existing["status"] != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Richiesta già risolta in stato '{existing['status']}'."
        )

    cur.execute(
        """
        UPDATE org3_approval_requests
        SET status = %s, resolution_note = %s, resolved_by = %s, resolved_at = NOW()
        WHERE id = %s
        RETURNING id, org_id, source_service, risk_class, title, description, payload, requested_by, status, resolution_note, resolved_by, resolved_at, created_at;
    """,
        (action, req.resolution_note, req.resolved_by, approval_id),
    )
    row = cur.fetchone()
    return ApprovalRequest(**dict(row))
