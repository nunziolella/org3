"""Router for 'Connect to Org3' Protocol.

Enables Structura, Memograph, and external clients to seamlessly authenticate,
inherit organizational hierarchy, delegation policies, cloud storage mapping,
and switch into Business Connected mode.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from org3.api.db import get_db

router = APIRouter(prefix="/v1/connect", tags=["Connect to Org3 Protocol"])


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


class ConnectRequest(BaseModel):
    token: str = Field(..., description="API Token (org3_sk_...) rilasciato da Org3 Platform")
    client_name: Optional[str] = Field(default="Structura OS", description="Nome applicazione client")
    client_version: Optional[str] = Field(default="1.0.0", description="Versione client")


class ConnectResponse(BaseModel):
    status: str = "connected"
    tier: str = "business"
    tenant: Dict[str, Any]
    member: Dict[str, Any]
    workspaces: List[Dict[str, Any]]
    delegation_policies: List[Dict[str, Any]]
    endpoints: Dict[str, str]
    features: Dict[str, bool]
    connected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


@router.post("", response_model=ConnectResponse)
def connect_to_org3(req: ConnectRequest, db=Depends(get_db)):
    """Protocollo 'Connect to Org3': valida il token e restituisce il contesto aziendale completo."""
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
            detail="Token Org3 non valido, revocato o organizzazione/membro disattivato.",
        )

    org_id = str(row["org_id"])
    member_id = str(row["member_id"])
    org_slug = row["org_slug"]
    plan = row["org_plan"]

    # 1. Recupera i workspaces configurati
    cur.execute(
        "SELECT id, name, storage_provider, storage_config, is_primary FROM org3_workspaces WHERE org_id = %s;",
        (org_id,),
    )
    workspaces = [dict(w) for w in cur.fetchall()]

    # 2. Recupera i contratti di delega attivi
    cur.execute(
        """
        SELECT id, name, scope, max_financial_authority, constraints, approval_gate
        FROM org3_delegation_policies
        WHERE org_id = %s AND (actor_id = %s OR is_revoked = false)
        ORDER BY created_at ASC;
    """,
        (org_id, member_id),
    )
    policies = [dict(p) for p in cur.fetchall()]

    # 3. Definisci feature flags in base al piano
    features = {
        "multi_cloud_storage": plan in ("business", "enterprise"),
        "delegation_engine": True,
        "hitl_approval_dispatch": plan in ("business", "enterprise"),
        "universal_mcp": True,
        "god_mode_bypass": bool(row["is_master"]),
    }

    # 4. Endpoints di sistema
    endpoints = {
        "mcp_gateway": f"/v1/mcp/{org_slug}",
        "storage_root": f"/v1/workspaces/{workspaces[0]['id'] if workspaces else ''}/storage",
        "approvals": "/v1/approvals",
        "delegation_evaluate": "/v1/delegation/evaluate",
    }

    # 5. Registra evento Outbox per auditing della connessione
    cur.execute(
        "INSERT INTO org3_outbox (aggregate_type, aggregate_id, event_type, payload) VALUES (%s, %s, %s, %s);",
        (
            'TOOL_CONNECTION',
            org_id,
            'CLIENT_CONNECTED',
            json.dumps({
                'client_name': req.client_name,
                'client_version': req.client_version,
                'member_id': member_id,
                'plan': plan
            })
        )
    )

    return ConnectResponse(
        status="connected",
        tier=plan,
        tenant={
            "id": org_id,
            "slug": org_slug,
            "name": row["org_name"],
            "plan": plan,
        },
        member={
            "id": member_id,
            "name": row["member_name"],
            "email": row["member_email"],
            "role": row["member_role"],
            "is_master": bool(row["is_master"]),
        },
        workspaces=workspaces,
        delegation_policies=policies,
        endpoints=endpoints,
        features=features,
    )


@router.get("/status")
def connect_status():
    """Quick ping per verificare la disponibilità del servizio Connect."""
    return {
        "service": "Org3 Connect Protocol",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/manifest")
def connect_manifest():
    """Restituisce il manifest dei tool e dei contratti supportati da Org3."""
    return {
        "protocol": "org3-connect-v1",
        "supported_clients": ["structura", "memograph", "claude_desktop", "cursor"],
        "mcp_tools": [
            "org3_list_domains",
            "org3_get_identity",
            "org3_evaluate_action",
            "org3_request_approval",
            "org3_list_pending_approvals",
            "org3_resolve_approval",
            "org3_list_storage_files",
        ],
        "persistent_domains_count": 10,
    }
