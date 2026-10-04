"""Org 3.0 Delegation Policy Engine (Soluzione Architetturale Caso CHRIMAT).

Consente di formalizzare contratti di delega espliciti e vincolanti tra attori (Founder/Manager -> Partner/Agenti):
- Chi può fare cosa.
- Entro quali massimali economici.
- Con quali vincoli tassativi (es. nessun impegno di IP, nessuna esclusiva, nessun vincolo su roadmap).
- Con quali meccanismi di escalation Human-in-the-Loop [HITL].
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DelegationConstraintType(str, Enum):
    """Tipologia di vincoli negativi o limitazioni contrattuali di delega."""
    NO_IP_CONCESSION = "NO_IP_CONCESSION"                # Divieto cessione o licenza esclusiva di IP
    NO_EXCLUSIVITY = "NO_EXCLUSIVITY"                    # Divieto concessione di esclusiva commerciale
    NO_ROADMAP_COMMITMENT = "NO_ROADMAP_COMMITMENT"      # Divieto impegno vincolante su date/feature di roadmap
    MAX_DISCOUNT_PERCENT = "MAX_DISCOUNT_PERCENT"        # Tetto massimo di sconto percentuale (es. 10.0)
    MAX_FINANCIAL_AMOUNT = "MAX_FINANCIAL_AMOUNT"        # Tetto massimo di valore economico per transazione
    REQUIRED_APPROVAL_GATE = "REQUIRED_APPROVAL_GATE"    # Richiede sempre conferma finale del delegante
    CUSTOM = "CUSTOM"                                    # Vincolo specifico parametrizzato


class DelegationConstraint(BaseModel):
    """Vincolo specifico applicato a una delega."""
    constraint_type: DelegationConstraintType
    value: Any = None                                    # es. 10.0 per max discount, o True
    description: str = ""


class DelegationPolicy(BaseModel):
    """Contratto formale di delega Org3."""
    id: str                                              # es. "del-chrimat-francesco-001"
    delegator_id: str                                    # ID dell'agente che conferisce la delega (es. Founder)
    delegate_id: str                                     # ID dell'agente/partner che riceve la delega
    allowed_actions: List[str]                           # es. ["send_commercial_proposal", "negotiate_lead"]
    scope: Optional[str] = None                          # es. "division:qubitdata", "partner:chrimat"
    constraints: List[DelegationConstraint] = Field(default_factory=list)
    financial_ceiling: Optional[float] = None            # Max valore economico autorizzabile in autonomia
    requires_hitl_escalation: bool = False               # Se True, le azioni generano sempre richiesta di review
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None                     # Data di scadenza ISO, se temporanea


class DelegationEvaluationResult(BaseModel):
    """Esito della valutazione di conformità di un'azione delegata."""
    allowed: bool
    requires_hitl: bool
    violations: List[str] = Field(default_factory=list)
    applied_constraints: List[str] = Field(default_factory=list)
    reason: str


class DelegationEngine:
    """Motore di calcolo e validazione delle Delegation Policies di Org3."""

    @staticmethod
    def evaluate_action(
        policy: DelegationPolicy,
        requested_action: str,
        financial_amount: Optional[float] = None,
        context_payload: Optional[Dict[str, Any]] = None
    ) -> DelegationEvaluationResult:
        """Valuta se l'azione richiesta rispetta la policy di delega."""
        payload = context_payload or {}
        violations: List[str] = []
        applied: List[str] = []

        if not policy.is_active:
            return DelegationEvaluationResult(
                allowed=False,
                requires_hitl=False,
                violations=["DELEGATION_POLICY_INACTIVE"],
                reason="La policy di delega specificata non è attiva."
            )

        # 1. Verifica se l'azione rientra tra quelle autorizzate
        if requested_action not in policy.allowed_actions and "*" not in policy.allowed_actions:
            return DelegationEvaluationResult(
                allowed=False,
                requires_hitl=False,
                violations=[f"ACTION_NOT_DELEGATED: {requested_action}"],
                reason=f"L'azione '{requested_action}' non è compresa tra le azioni delegate."
            )

        # 2. Verifica del massimale economico
        if financial_amount is not None:
            if policy.financial_ceiling is not None and financial_amount > policy.financial_ceiling:
                violations.append(
                    f"FINANCIAL_CEILING_EXCEEDED: richiesto {financial_amount}€, limite {policy.financial_ceiling}€"
                )

        # 3. Verifica dei singoli vincoli rigidi
        requires_hitl = policy.requires_hitl_escalation

        for c in policy.constraints:
            applied.append(c.constraint_type.value)

            if c.constraint_type == DelegationConstraintType.NO_IP_CONCESSION:
                if payload.get("concedes_ip", False) or payload.get("transfers_copyright", False):
                    violations.append("VIOLATION_NO_IP_CONCESSION: La proposta include cessione o licenza esclusiva di IP.")

            elif c.constraint_type == DelegationConstraintType.NO_EXCLUSIVITY:
                if payload.get("grants_exclusivity", False):
                    violations.append("VIOLATION_NO_EXCLUSIVITY: La proposta include accordi di esclusiva territoriale o commerciale.")

            elif c.constraint_type == DelegationConstraintType.NO_ROADMAP_COMMITMENT:
                if payload.get("commits_to_fixed_roadmap", False) or payload.get("binding_sla_dates", False):
                    violations.append("VIOLATION_NO_ROADMAP_COMMITMENT: La proposta impegna date vincolanti sulla roadmap di sviluppo.")

            elif c.constraint_type == DelegationConstraintType.MAX_DISCOUNT_PERCENT:
                discount = payload.get("discount_percent", 0.0)
                max_allowed = float(c.value) if c.value is not None else 0.0
                if discount > max_allowed:
                    violations.append(
                        f"VIOLATION_MAX_DISCOUNT: applicato sconto del {discount}%, limite massimo consentito {max_allowed}%."
                    )

            elif c.constraint_type == DelegationConstraintType.REQUIRED_APPROVAL_GATE:
                requires_hitl = True

        if violations:
            return DelegationEvaluationResult(
                allowed=False,
                requires_hitl=requires_hitl,
                violations=violations,
                applied_constraints=applied,
                reason="L'operazione vìola uno o più vincoli inderogabili della delega."
            )

        return DelegationEvaluationResult(
            allowed=True,
            requires_hitl=requires_hitl,
            violations=[],
            applied_constraints=applied,
            reason="Azione pienamente conforme ai contratti di delega."
        )
