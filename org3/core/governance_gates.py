"""Org 3.0 Governance Gates & Risk Classification (Classi A/B/C/D).

Allineato all'architettura MAS e Work Management di Structura:
- Classe A: Auto-approve (note, metadati, correzioni ortografiche)
- Classe B: Evidence-backed (chiusura task con evidenza oggettiva verificabile)
- Classe C: Human-in-the-Loop [HITL] (creazione obiettivi, cambio scope, proposte commerciali, spese)
- Classe D: Master Assoluto Change Control (ontologia, schemi governance, invarianti hard)
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from org3.core.ontology import Agent, Role
from org3.core.delegation import DelegationEvaluationResult


class MutationRiskClass(str, Enum):
    """Matrice di Rischio delle Mutazioni e delle Azioni Operative."""
    CLASS_A_AUTO = "CLASS_A_AUTO"            # Auto-approvazione immediata
    CLASS_B_EVIDENCE = "CLASS_B_EVIDENCE"    # Approvabile automaticamente solo con evidenza verificabile
    CLASS_C_HITL = "CLASS_C_HITL"            # Richiede Gate Umano obbligatorio (Human-in-the-Loop)
    CLASS_D_MASTER = "CLASS_D_MASTER"        # Riservato esclusivamente al Master Assoluto (Founder)


class GateDecisionType(str, Enum):
    """Esito decisionale del gate di governance."""
    APPROVED_AUTO = "APPROVED_AUTO"
    APPROVED_GOD_MODE = "APPROVED_GOD_MODE"
    ESCALATE_HITL = "ESCALATE_HITL"
    BLOCKED_UNAUTHORIZED = "BLOCKED_UNAUTHORIZED"
    BLOCKED_POLICY_VIOLATION = "BLOCKED_POLICY_VIOLATION"


class GovernanceGateDecision(BaseModel):
    """Decisione strutturata prodotta dal Governance Gate."""
    decision: GateDecisionType
    allowed_to_proceed: bool
    requires_human_approval: bool
    risk_class: MutationRiskClass
    actor_id: str
    reasons: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GovernanceGateEvaluator:
    """Valutatore canonico delle politiche di autorizzazione e rischio in Org3."""

    @staticmethod
    def evaluate(
        actor: Agent,
        role: Role,
        risk_class: MutationRiskClass,
        has_verifiable_evidence: bool = False,
        delegation_result: Optional[DelegationEvaluationResult] = None,
        action_name: str = "generic_action"
    ) -> GovernanceGateDecision:
        """Valuta se l'azione dell'agente può essere eseguita, richiede HITL o è bloccata."""

        # 1. Master Assoluto (God Mode): bypassa tutti i vincoli ordinari
        if actor.is_master:
            return GovernanceGateDecision(
                decision=GateDecisionType.APPROVED_GOD_MODE,
                allowed_to_proceed=True,
                requires_human_approval=False,
                risk_class=risk_class,
                actor_id=actor.id,
                reasons=["Master Assoluto autorizzato con pieni poteri (God Mode)."]
            )

        # 2. Controllo esito delega (se applicata)
        if delegation_result is not None:
            if not delegation_result.allowed:
                return GovernanceGateDecision(
                    decision=GateDecisionType.BLOCKED_POLICY_VIOLATION,
                    allowed_to_proceed=False,
                    requires_human_approval=False,
                    risk_class=risk_class,
                    actor_id=actor.id,
                    reasons=delegation_result.violations or [delegation_result.reason]
                )
            if delegation_result.requires_hitl:
                return GovernanceGateDecision(
                    decision=GateDecisionType.ESCALATE_HITL,
                    allowed_to_proceed=False,
                    requires_human_approval=True,
                    risk_class=risk_class,
                    actor_id=actor.id,
                    reasons=["La policy di delega richiede obbligatoriamente approvazione umana (HITL)."]
                )

        # 3. Valutazione per Classe di Rischio
        if risk_class == MutationRiskClass.CLASS_D_MASTER:
            return GovernanceGateDecision(
                decision=GateDecisionType.BLOCKED_UNAUTHORIZED,
                allowed_to_proceed=False,
                requires_human_approval=False,
                risk_class=risk_class,
                actor_id=actor.id,
                reasons=["Classe D riservata esclusivamente al Master Assoluto (Founder). Azione respinta."]
            )

        if risk_class == MutationRiskClass.CLASS_C_HITL:
            return GovernanceGateDecision(
                decision=GateDecisionType.ESCALATE_HITL,
                allowed_to_proceed=False,
                requires_human_approval=True,
                risk_class=risk_class,
                actor_id=actor.id,
                reasons=[f"Azione '{action_name}' classificata Classe C (alto impatto): richiesto Human-in-the-Loop."]
            )

        if risk_class == MutationRiskClass.CLASS_B_EVIDENCE:
            if has_verifiable_evidence:
                return GovernanceGateDecision(
                    decision=GateDecisionType.APPROVED_AUTO,
                    allowed_to_proceed=True,
                    requires_human_approval=False,
                    risk_class=risk_class,
                    actor_id=actor.id,
                    reasons=["Classe B approvata automaticamente con evidenza verificabile prodotta."]
                )
            else:
                return GovernanceGateDecision(
                    decision=GateDecisionType.ESCALATE_HITL,
                    allowed_to_proceed=False,
                    requires_human_approval=True,
                    risk_class=risk_class,
                    actor_id=actor.id,
                    reasons=["Classe B priva di evidenza verificabile: richiesta escalation a revisione umana."]
                )

        # Classe A: Auto-approvazione
        return GovernanceGateDecision(
            decision=GateDecisionType.APPROVED_AUTO,
            allowed_to_proceed=True,
            requires_human_approval=False,
            risk_class=risk_class,
            actor_id=actor.id,
            reasons=["Classe A: modifica a basso rischio approvata in autonomia."]
        )
