"""Router for Delegation Policy Engine and Real-Time Evaluation in Org3 Platform."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from org3.api.db import get_db
from org3.core.delegation import (
    DelegationConstraint,
    DelegationConstraintType,
    DelegationEngine,
    DelegationPolicy,
)
from org3.core.governance_gates import MutationRiskClass, GovernanceGateEvaluator
from org3.models.multitenant import DelegationPolicyRecord

router = APIRouter(prefix="/v1/delegation", tags=["Delegation & Policy Engine"])


class CreatePolicyRequest(BaseModel):
    org_id: str
    actor_id: str
    name: str = Field(..., max_length=255)
    scope: str = Field(..., max_length=128)
    max_financial_authority: float = Field(default=0.00, ge=0.0)
    constraints: List[str] = Field(default_factory=list, description="Lista vincoli: NO_IP_CONCESSION, NO_EXCLUSIVITY, etc.")
    approval_gate: str = Field(default="CLASS_C")


class EvaluateActionRequest(BaseModel):
    org_id: str
    actor_id: str
    action: str
    requested_amount: Optional[float] = None
    proposed_discount_pct: Optional[float] = None
    touches_ip: bool = False
    grants_exclusivity: bool = False
    commits_roadmap: bool = False


class EvaluateActionResponse(BaseModel):
    allowed: bool
    requires_hitl: bool
    governance_gate: str  # CLASS_A, CLASS_B, CLASS_C, CLASS_D
    violations: List[str] = Field(default_factory=list)
    applied_constraints: List[str] = Field(default_factory=list)
    reason: str


@router.post("/policies", response_model=DelegationPolicyRecord, status_code=status.HTTP_201_CREATED)
def create_policy(req: CreatePolicyRequest, db=Depends(get_db)):
    """Formalizza un nuovo contratto di delega vincolante con vincoli negativi anti-Chrimat."""
    cur = db.cursor()
    # Verifica esistenza attore
    cur.execute("SELECT id, org_id FROM org3_members WHERE id = %s AND org_id = %s;", (req.actor_id, req.org_id))
    if not cur.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membro o Organizzazione non validi.")

    cur.execute(
        """
        INSERT INTO org3_delegation_policies (org_id, actor_id, name, scope, max_financial_authority, constraints, approval_gate)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, org_id, actor_id, name, scope, max_financial_authority, constraints, approval_gate, is_revoked, created_at;
    """,
        (
            req.org_id,
            req.actor_id,
            req.name.strip(),
            req.scope.strip(),
            req.max_financial_authority,
            json.dumps(req.constraints),
            req.approval_gate.strip().upper(),
        ),
    )
    row = cur.fetchone()
    return DelegationPolicyRecord(**dict(row))


@router.get("/policies", response_model=List[DelegationPolicyRecord])
def list_policies(org_id: str, actor_id: Optional[str] = None, is_active: bool = True, db=Depends(get_db)):
    """Elenca i contratti di delega attivi per un'organizzazione."""
    cur = db.cursor()
    query = """
        SELECT id, org_id, actor_id, name, scope, max_financial_authority, constraints, approval_gate, is_revoked, created_at
        FROM org3_delegation_policies
        WHERE org_id = %s
    """
    params = [org_id]
    if actor_id:
        query += " AND actor_id = %s"
        params.append(actor_id)
    if is_active:
        query += " AND is_revoked = false"
    query += " ORDER BY created_at DESC;"

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    return [DelegationPolicyRecord(**dict(r)) for r in rows]


@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_policy(policy_id: str, db=Depends(get_db)):
    """Revoca formalmente un contratto di delega."""
    cur = db.cursor()
    cur.execute("UPDATE org3_delegation_policies SET is_revoked = true WHERE id = %s RETURNING id;", (policy_id,))
    if not cur.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contratto di delega non trovato.")
    return None


@router.post("/evaluate", response_model=EvaluateActionResponse)
def evaluate_delegation(req: EvaluateActionRequest, db=Depends(get_db)):
    """Valuta in tempo reale se un'azione è autorizzata, violata o richiede approvazione HITL."""
    cur = db.cursor()

    # 1. Recupero Membro e verifica God Mode
    cur.execute("SELECT id, email, role, is_master, is_active FROM org3_members WHERE id = %s AND org_id = %s;", (req.actor_id, req.org_id))
    member = cur.fetchone()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attore non censito nell'organizzazione.")

    if not member["is_active"]:
        return EvaluateActionResponse(
            allowed=False,
            requires_hitl=False,
            governance_gate="CLASS_D",
            violations=["ATTORE_DISABILITATO: Il membro è disattivato"],
            reason="Attore non autorizzato (disattivato).",
        )

    # Invariante God Mode per Nunzio Lella: bypass totale
    if member["is_master"]:
        return EvaluateActionResponse(
            allowed=True,
            requires_hitl=False,
            governance_gate="CLASS_A",
            violations=[],
            applied_constraints=[],
            reason="God Mode attivo: il Founder possiede autorità assoluta immediata.",
        )

    # 2. Recupero dei contratti di delega attivi
    cur.execute(
        """
        SELECT id, name, scope, max_financial_authority, constraints, approval_gate
        FROM org3_delegation_policies
        WHERE org_id = %s AND actor_id = %s AND is_revoked = false
        ORDER BY max_financial_authority DESC;
    """,
        (req.org_id, req.actor_id),
    )
    policies = cur.fetchall()

    if not policies:
        return EvaluateActionResponse(
            allowed=False,
            requires_hitl=True,
            governance_gate="CLASS_C",
            violations=["NO_DELEGATION_POLICY: Nessun contratto di delega attivo trovato per l'attore"],
            reason="Nessuna delega concessa: l'azione richiede autorizzazione umana (Gate Classe C).",
        )

    # 3. Valutazione con il core DelegationEngine (Zero Duplication!)
    # Seleziona la policy con lo scope corrispondente o la più ampia
    matched_policy_row = policies[0]
    for p in policies:
        if p["scope"] and p["scope"].lower() in req.action.lower():
            matched_policy_row = p
            break

    # Converti i vincoli in oggetti DelegationConstraint
    raw_constraints = matched_policy_row["constraints"]
    if isinstance(raw_constraints, str):
        raw_constraints = json.loads(raw_constraints)

    parsed_constraints = []
    for c in raw_constraints:
        if isinstance(c, str):
            try:
                ctype = DelegationConstraintType(c)
                parsed_constraints.append(DelegationConstraint(constraint_type=ctype, value=True))
            except ValueError:
                parsed_constraints.append(DelegationConstraint(constraint_type=DelegationConstraintType.CUSTOM, description=c))
        elif isinstance(c, dict):
            parsed_constraints.append(DelegationConstraint(**c))

    core_policy = DelegationPolicy(
        id=str(matched_policy_row["id"]),
        delegator_id=str(req.org_id),
        delegate_id=str(req.actor_id),
        allowed_actions=[req.action],
        scope=matched_policy_row["scope"],
        constraints=parsed_constraints,
        financial_ceiling=float(matched_policy_row["max_financial_authority"]) if matched_policy_row["max_financial_authority"] else None,
        requires_hitl_escalation=(matched_policy_row["approval_gate"] in ["CLASS_C", "CLASS_D"]),
    )

    context_payload = {
        "concedes_ip": req.touches_ip,
        "transfers_copyright": req.touches_ip,
        "grants_exclusivity": req.grants_exclusivity,
        "commits_to_fixed_roadmap": req.commits_roadmap,
        "discount_percent": req.proposed_discount_pct or 0.0,
    }

    eval_result = DelegationEngine.evaluate_action(
        policy=core_policy,
        requested_action=req.action,
        financial_amount=req.requested_amount,
        context_payload=context_payload,
    )

    gate = matched_policy_row["approval_gate"]
    if not eval_result.allowed:
        gate = "CLASS_C"

    return EvaluateActionResponse(
        allowed=eval_result.allowed,
        requires_hitl=eval_result.requires_hitl,
        governance_gate=gate,
        violations=eval_result.violations,
        applied_constraints=eval_result.applied_constraints,
        reason=eval_result.reason,
    )
