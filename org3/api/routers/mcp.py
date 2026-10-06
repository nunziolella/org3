"""Universal Multi-Tenant MCP Gateway for Org3 Platform.

Exposes JSON-RPC 2.0 Model Context Protocol endpoints at `/v1/mcp/{tenant_slug}`
enabling Claude Desktop, Cursor, PAI, and external AI agents to query storage,
evaluate delegation policies, submit HITL approvals, and check IAM permissions.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from org3.api.db import get_db
from org3.api.routers.delegation import evaluate_delegation as api_evaluate_action, EvaluateActionRequest
from org3.models.multitenant import Workspace
from org3.notifications.dispatcher import get_dispatcher
from org3.storage.base import CANONICAL_DOMAINS
from org3.storage.factory import StorageAdapterFactory

logger = logging.getLogger("org3.mcp")

router = APIRouter(prefix="/v1/mcp", tags=["Universal MCP Gateway"])


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Any] = 1
    method: str
    params: Optional[Dict[str, Any]] = None


def authenticate_mcp_caller(
    tenant_slug: str,
    authorization: Optional[str] = Header(None),
    token_param: Optional[str] = Query(None, alias="token"),
    db=None,
) -> Dict[str, Any]:
    """Valida il token API e assicura che appartenga al tenant_slug richiesto."""
    raw_token = None
    if authorization and authorization.lower().startswith("bearer "):
        raw_token = authorization[7:].strip()
    elif token_param:
        raw_token = token_param.strip()

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header Authorization Bearer o parametro token mancante.",
        )

    token_h = hash_token(raw_token)
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
            detail="Token Org3 non valido, scaduto o membro/tenant disattivato.",
        )

    if row["org_slug"].lower() != tenant_slug.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Token non autorizzato per il tenant '{tenant_slug}'.",
        )

    return dict(row)


# Tools Schema Definition
MCP_TOOLS = [
    {
        "name": "org3_list_domains",
        "description": "List the 10 canonical persistent storage domains defined by the Org3 architecture.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "org3_get_identity",
        "description": "Get current caller's identity, role, tenant, and God-Mode status.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "org3_evaluate_action",
        "description": "Evaluate an intended action against Org3 delegation policies (CHRIMAT constraints: no IP concession, no exclusivity, max financial cap).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "e.g. 'quote.create', 'deploy.prod', 'roadmap.commit'"},
                "financial_impact": {"type": "number", "description": "Monetary value involved in EUR (optional)"},
                "parameters": {"type": "object", "description": "Contextual parameters to validate"},
            },
            "required": ["action"],
        },
    },
    {
        "name": "org3_request_approval",
        "description": "Submit a Human-in-the-Loop (HITL) approval request. Automatically alerts Nunzio's Telegram with a 1-click deep-link.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Short summary of the request"},
                "description": {"type": "string", "description": "Detailed explanation of why approval is needed"},
                "risk_class": {"type": "string", "enum": ["A", "B", "C", "D"], "default": "C"},
                "payload": {"type": "object", "description": "Payload with changes/diff to approve"},
            },
            "required": ["title", "description"],
        },
    },
    {
        "name": "org3_list_pending_approvals",
        "description": "List pending HITL approval requests for the organization.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "risk_class": {"type": "string", "enum": ["A", "B", "C", "D"]},
            },
        },
    },
    {
        "name": "org3_resolve_approval",
        "description": "Approve or reject a pending approval request (requires Master Assoluto or authorized role).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "approval_id": {"type": "string", "description": "UUID of the approval request"},
                "action": {"type": "string", "enum": ["APPROVED", "REJECTED"]},
                "resolution_note": {"type": "string"},
            },
            "required": ["approval_id", "action"],
        },
    },
    {
        "name": "org3_list_storage_files",
        "description": "List stored files in one of the 10 persistent domains via Org3 Anti-Quota Shield.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain_code": {"type": "string", "description": "Code 01..10, e.g. '01_CORPORATE', '05_COMMERCIAL_GTM'"},
                "prefix": {"type": "string", "description": "Optional subdirectory prefix"},
            },
            "required": ["domain_code"],
        },
    },
]


@router.post("/{tenant_slug}")
async def handle_mcp_jsonrpc(
    tenant_slug: str,
    req: JsonRpcRequest,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None),
    db=Depends(get_db),
):
    """Gestisce chiamate JSON-RPC 2.0 al gateway MCP per lo specifico tenant."""
    # Autenticazione caller
    caller = authenticate_mcp_caller(tenant_slug, authorization, token, db)

    method = req.method
    params = req.params or {}

    # 1. initialize
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False},
                },
                "serverInfo": {
                    "name": "org3-universal-mcp",
                    "version": "1.0.0",
                    "tenant": caller["org_slug"],
                },
            },
        }

    # 2. notifications/initialized
    elif method in ("notifications/initialized", "initialized"):
        return {"jsonrpc": "2.0", "id": req.id, "result": {}}

    # 3. tools/list
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "result": {"tools": MCP_TOOLS},
        }

    # 4. tools/call
    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})

        cur = db.cursor()
        org_id = str(caller["org_id"])
        member_id = str(caller["member_id"])

        result_payload = None

        if tool_name == "org3_list_domains":
            domains_list = [
                {"code": d["code"], "folder_name": d["name"], "title": d["title"], "description": d["description"]}
                for d in CANONICAL_DOMAINS.values()
            ]
            result_payload = {"domains": domains_list}

        elif tool_name == "org3_get_identity":
            result_payload = {
                "tenant": {
                    "id": org_id,
                    "slug": caller["org_slug"],
                    "name": caller["org_name"],
                    "plan": caller["org_plan"],
                },
                "member": {
                    "id": member_id,
                    "name": caller["member_name"],
                    "email": caller["member_email"],
                    "role": caller["member_role"],
                    "is_master": bool(caller["is_master"]),
                },
            }

        elif tool_name == "org3_evaluate_action":
            action = args.get("action", "")
            financial_impact = float(args.get("financial_impact", 0.0) or 0.0)
            action_params = args.get("parameters", {})

            eval_req = EvaluateActionRequest(
                org_id=org_id,
                actor_id=member_id,
                action=action,
                requested_amount=financial_impact,
                proposed_discount_pct=float(action_params.get("discount_pct", 0.0) or 0.0),
                touches_ip=bool(action_params.get("touches_ip", False)),
                grants_exclusivity=bool(action_params.get("grants_exclusivity", False)),
                commits_roadmap=bool(action_params.get("commits_roadmap", False)),
            )
            eval_res = api_evaluate_action(eval_req, db=db)
            result_payload = {
                "authorized": eval_res.allowed,
                "reason": eval_res.reason,
                "risk_class": eval_res.governance_gate,
                "violations": eval_res.violations,
                "requires_hitl": eval_res.requires_hitl,
                "applied_constraints": eval_res.applied_constraints,
            }

        elif tool_name == "org3_request_approval":
            title = args.get("title")
            description = args.get("description")
            risk_class = args.get("risk_class", "C").upper()
            payload = args.get("payload", {})

            cur.execute(
                """
                INSERT INTO org3_approval_requests (org_id, source_service, risk_class, title, description, payload, requested_by, status)
                VALUES (%s, 'universal_mcp_gateway', %s, %s, %s, %s, %s, 'PENDING')
                RETURNING id, org_id, source_service, risk_class, title, description, payload, requested_by, status, created_at;
            """,
                (org_id, risk_class, title.strip(), description.strip(), json.dumps(payload), member_id),
            )
            appr_row = cur.fetchone()

            # Trigger Dispatcher
            fin_val = None
            if isinstance(payload, dict) and "amount" in payload:
                fin_val = float(payload["amount"])

            dispatch_res = get_dispatcher().dispatch_approval_alert(
                approval_id=str(appr_row["id"]),
                org_slug=caller["org_slug"],
                org_name=caller["org_name"],
                title=title,
                description=description,
                risk_class=risk_class,
                source_service="universal_mcp_gateway",
                requested_by_name=caller["member_name"],
                financial_value=fin_val,
            )

            result_payload = {
                "approval_id": str(appr_row["id"]),
                "status": "PENDING",
                "notification_dispatched": dispatch_res["dispatched"],
                "deep_link": dispatch_res["deep_link"],
            }

        elif tool_name == "org3_list_pending_approvals":
            risk_class = args.get("risk_class")
            q = "SELECT id, title, description, risk_class, source_service, status, created_at FROM org3_approval_requests WHERE org_id = %s AND status = 'PENDING'"
            pms = [org_id]
            if risk_class:
                q += " AND risk_class = %s"
                pms.append(risk_class.upper())
            q += " ORDER BY created_at DESC;"
            cur.execute(q, tuple(pms))
            rows = [dict(r) for r in cur.fetchall()]
            result_payload = {"pending_approvals": rows}

        elif tool_name == "org3_resolve_approval":
            appr_id = args.get("approval_id")
            action = args.get("action", "").upper()
            note = args.get("resolution_note")

            if not caller["is_master"] and caller["member_role"] not in ("FOUNDER_GODMODE", "CEO", "TECH_LEAD"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo il Master Assoluto o ruoli apicali possono risolvere le approvazioni.",
                )

            cur.execute(
                """
                UPDATE org3_approval_requests
                SET status = %s, resolution_note = %s, resolved_by = %s, resolved_at = NOW()
                WHERE id = %s AND org_id = %s
                RETURNING id, status, resolution_note, resolved_at;
            """,
                (action, note, member_id, appr_id, org_id),
            )
            updated = cur.fetchone()
            if not updated:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Richiesta di approvazione non trovata.")

            result_payload = {"approval_id": str(updated["id"]), "status": updated["status"], "resolved_at": updated["resolved_at"].isoformat()}

        elif tool_name == "org3_list_storage_files":
            domain_code = args.get("domain_code")
            prefix = args.get("prefix", "")

            # Ottieni adapter primario per workspace
            cur.execute(
                "SELECT id, org_id, name, storage_provider, storage_config, is_primary, created_at FROM org3_workspaces WHERE org_id = %s ORDER BY is_primary DESC LIMIT 1;",
                (org_id,),
            )
            w_row = cur.fetchone()
            if not w_row:
                result_payload = {"files": [], "warning": "Nessun workspace configurato."}
            else:
                ws = Workspace(**dict(w_row))
                adapter = StorageAdapterFactory.get_adapter_for_workspace(ws)
                items = await adapter.list_domain_items(domain_code, prefix=prefix)
                result_payload = {"domain": domain_code, "files": [it.model_dump() for it in items]}

        else:
            return {
                "jsonrpc": "2.0",
                "id": req.id,
                "error": {"code": -32601, "message": f"Tool '{tool_name}' non trovato."},
            }

        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result_payload, indent=2, default=str),
                    }
                ]
            },
        }

    else:
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "error": {"code": -32601, "message": f"Metodo JSON-RPC '{method}' non supportato."},
        }
