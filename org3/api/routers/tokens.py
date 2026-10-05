"""Router for Org3 Connect Tokens & Tool Authentication."""

from __future__ import annotations

import hashlib
import json
import secrets
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from org3.api.db import get_db
from org3.models.multitenant import ApiToken

router = APIRouter(prefix="/v1/tokens", tags=["Tokens & Org3 Connect"])


class CreateTokenRequest(BaseModel):
    org_id: str
    member_id: str
    name: str = Field(..., max_length=255, description="Nome identificativo del client (es. 'Structura OS Staging')")
    allowed_scopes: List[str] = Field(default_factory=lambda: ["read", "write"])


class CreateTokenResponse(BaseModel):
    token: str = Field(..., description="Chiave segreta da mostrare una sola volta al client")
    api_token: ApiToken


class ValidateTokenRequest(BaseModel):
    token: str


class ValidateTokenResponse(BaseModel):
    valid: bool
    org_id: str
    org_slug: str
    org_name: str
    plan: str
    member_id: str
    member_name: str
    member_email: str
    member_role: str
    is_master: bool
    allowed_scopes: List[str]


def hash_token(raw_token: str) -> str:
    """Calcola l'hash crittografico SHA256 del token."""
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


@router.post("", response_model=CreateTokenResponse, status_code=status.HTTP_201_CREATED)
def create_token(req: CreateTokenRequest, db=Depends(get_db)):
    """Genera una nuova chiave API Org3 Connect per un membro."""
    cur = db.cursor()
    # Verifica esistenza membro nell'organizzazione
    cur.execute("SELECT id FROM org3_members WHERE id = %s AND org_id = %s;", (req.member_id, req.org_id))
    if not cur.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membro o organizzazione non validi.")

    # Genera token crittograficamente sicuro (prefisso org3_sk_...)
    raw_token = f"org3_sk_{secrets.token_urlsafe(32)}"
    token_h = hash_token(raw_token)

    cur.execute(
        """
        INSERT INTO org3_api_tokens (org_id, member_id, token_hash, name, allowed_scopes)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, org_id, member_id, token_hash, name, allowed_scopes, expires_at, created_at;
    """,
        (req.org_id, req.member_id, token_h, req.name.strip(), json.dumps(req.allowed_scopes)),
    )
    row = cur.fetchone()
    return CreateTokenResponse(token=raw_token, api_token=ApiToken(**dict(row)))


@router.post("/validate", response_model=ValidateTokenResponse)
def validate_token(req: ValidateTokenRequest, db=Depends(get_db)):
    """Valida un token Org3 Connect inviato da Structura, Memograph o client MCP."""
    token_h = hash_token(req.token)
    cur = db.cursor()

    cur.execute(
        """
        SELECT 
            t.id as token_id, t.allowed_scopes,
            m.id as member_id, m.name as member_name, m.email as member_email, m.role as member_role, m.is_master, m.is_active as member_active,
            o.id as org_id, o.slug as org_slug, o.name as org_name, o.plan as org_plan, o.is_active as org_active
        FROM org3_api_tokens t
        JOIN org3_members m ON t.member_id = m.id
        JOIN org3_organizations o ON t.org_id = o.id
        WHERE t.token_hash = %s;
    """,
        (token_h,),
    )
    row = cur.fetchone()
    if not row or not row["member_active"] or not row["org_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token non valido o organizzazione/membro disattivato."
        )

    scopes = row["allowed_scopes"]
    if isinstance(scopes, str):
        scopes = json.loads(scopes)

    return ValidateTokenResponse(
        valid=True,
        org_id=str(row["org_id"]),
        org_slug=row["org_slug"],
        org_name=row["org_name"],
        plan=row["org_plan"],
        member_id=str(row["member_id"]),
        member_name=row["member_name"],
        member_email=row["member_email"],
        member_role=row["member_role"],
        is_master=row["is_master"],
        allowed_scopes=scopes,
    )


@router.get("", response_model=List[ApiToken])
def list_tokens(org_id: str, db=Depends(get_db)):
    """Elenca i token configurati per un'organizzazione."""
    cur = db.cursor()
    cur.execute(
        """
        SELECT id, org_id, member_id, token_hash, name, allowed_scopes, expires_at, created_at
        FROM org3_api_tokens
        WHERE org_id = %s
        ORDER BY created_at DESC;
    """,
        (org_id,),
    )
    rows = cur.fetchall()
    return [ApiToken(**dict(r)) for r in rows]


@router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_token(token_id: str, db=Depends(get_db)):
    """Revoca una chiave API."""
    cur = db.cursor()
    cur.execute("DELETE FROM org3_api_tokens WHERE id = %s RETURNING id;", (token_id,))
    if not cur.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token non trovato.")
    return None
