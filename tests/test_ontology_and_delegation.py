"""Exhaustive test suite for Org 3.0 Core Ontology, Delegation Engine, and Virtual Memory Lenses."""

import pytest
from org3 import (
    FunctionalDomain,
    MemoryAuthority,
    DocumentLifecycleStatus,
    OrgStructureType,
    AgentType,
    ActionPermission,
    Role,
    Agent,
    Division,
    OrganizationalUnit,
    PersistentArtifactReference,
    DelegationConstraintType,
    DelegationConstraint,
    DelegationPolicy,
    DelegationEvaluationResult,
    DelegationEngine,
    VirtualMemoryView,
    VirtualMemoryLens,
    MutationRiskClass,
    GateDecisionType,
    GovernanceGateDecision,
    GovernanceGateEvaluator,
)


def test_functional_domains_and_authority():
    """Verifica che i 10 domini del Persistent Information Layer e le 5 autorità siano mappati."""
    assert FunctionalDomain.D01_CORPORATE.value == "01_CORPORATE"
    assert FunctionalDomain.D02_STRATEGY.value == "02_STRATEGY"
    assert FunctionalDomain.D03_ORGANIZATION_GOVERNANCE.value == "03_ORGANIZATION_GOVERNANCE"
    assert FunctionalDomain.D04_ADMINISTRATION_FINANCE.value == "04_ADMINISTRATION_FINANCE"
    assert FunctionalDomain.D05_TECHNOLOGY_DATA.value == "05_TECHNOLOGY_DATA"
    assert FunctionalDomain.D06_PRODUCT.value == "06_PRODUCT"
    assert FunctionalDomain.D07_MARKET_COMMERCIAL.value == "07_MARKET_COMMERCIAL"
    assert FunctionalDomain.D08_RESEARCH_KNOWLEDGE.value == "08_RESEARCH_KNOWLEDGE"
    assert FunctionalDomain.D09_MANAGEMENT_MEMORY.value == "09_MANAGEMENT_MEMORY"
    assert FunctionalDomain.D10_OPERATIONS_RECORDS.value == "10_OPERATIONS_RECORDS"

    # 5 Autorità del MEMORY_REGISTRY
    assert MemoryAuthority.RAW_MEMORY.value == "raw_memory"
    assert MemoryAuthority.META_MEMORY.value == "meta_memory"
    assert MemoryAuthority.CANONICAL_MEMORY.value == "canonical_memory"
    assert MemoryAuthority.DECISION_MEMORY.value == "decision_memory"
    assert MemoryAuthority.OPERATIONAL_MEMORY.value == "operational_memory"


def test_roles_agents_and_master_mode():
    """Verifica la creazione di ruoli, agenti e il comportamento del Master Assoluto (God Mode)."""
    perm = ActionPermission(resource="commercial_proposal", action="create_draft", scope="division:qubitdata")
    role_lead = Role(
        id="ROLE_TECH_LEAD",
        name="Technical Lead",
        department_level="L2_TECH_SDLC",
        description="Oversees architecture and technical decisions",
        permissions=[perm],
        decision_rights=["approve_tech_pr", "architectural_review"]
    )
    assert role_lead.id == "ROLE_TECH_LEAD"
    assert len(role_lead.permissions) == 1

    # Agente normale
    agent_dev = Agent(
        id="agent-dev-01",
        name="Developer One",
        agent_type=AgentType.HUMAN,
        assigned_roles=["ROLE_TECH_LEAD"],
        is_master=False
    )
    assert not agent_dev.is_master

    # Master Assoluto (Founder)
    founder = Agent(
        id="agent-nunzio",
        name="Nunzio Lella",
        agent_type=AgentType.HUMAN,
        email="01nunzio.lella@gmail.com",
        assigned_roles=["ROLE_FOUNDER_CEO"],
        is_master=True
    )
    assert founder.is_master


def test_chrimat_delegation_success():
    """Verifica che una proposta commerciale pienamente conforme alla delega venga autorizzata."""
    policy = DelegationPolicy(
        id="del-chrimat-001",
        delegator_id="agent-nunzio",
        delegate_id="agent-francesco",
        allowed_actions=["send_commercial_proposal"],
        scope="division:qubitdata",
        constraints=[
            DelegationConstraint(constraint_type=DelegationConstraintType.NO_IP_CONCESSION, description="Nessuna cessione IP"),
            DelegationConstraint(constraint_type=DelegationConstraintType.NO_EXCLUSIVITY, description="Nessuna esclusiva"),
            DelegationConstraint(constraint_type=DelegationConstraintType.NO_ROADMAP_COMMITMENT, description="Nessun vincolo roadmap"),
            DelegationConstraint(constraint_type=DelegationConstraintType.MAX_DISCOUNT_PERCENT, value=10.0, description="Max 10% sconto"),
        ],
        financial_ceiling=30000.0,
        requires_hitl_escalation=False,
    )

    clean_payload = {
        "concedes_ip": False,
        "grants_exclusivity": False,
        "commits_to_fixed_roadmap": False,
        "discount_percent": 8.0
    }

    result = DelegationEngine.evaluate_action(
        policy=policy,
        requested_action="send_commercial_proposal",
        financial_amount=19500.0,
        context_payload=clean_payload
    )

    assert result.allowed is True
    assert result.requires_hitl is False
    assert len(result.violations) == 0


def test_chrimat_delegation_violations():
    """Verifica che le violazioni (IP, Esclusiva, Roadmap, Sconto, Soffitto Finanziario) vengano bloccate."""
    policy = DelegationPolicy(
        id="del-chrimat-001",
        delegator_id="agent-nunzio",
        delegate_id="agent-francesco",
        allowed_actions=["send_commercial_proposal"],
        scope="division:qubitdata",
        constraints=[
            DelegationConstraint(constraint_type=DelegationConstraintType.NO_IP_CONCESSION),
            DelegationConstraint(constraint_type=DelegationConstraintType.NO_EXCLUSIVITY),
            DelegationConstraint(constraint_type=DelegationConstraintType.NO_ROADMAP_COMMITMENT),
            DelegationConstraint(constraint_type=DelegationConstraintType.MAX_DISCOUNT_PERCENT, value=10.0),
        ],
        financial_ceiling=25000.0,
    )

    # Violazione 1: Cessione IP
    res_ip = DelegationEngine.evaluate_action(
        policy=policy,
        requested_action="send_commercial_proposal",
        financial_amount=10000.0,
        context_payload={"concedes_ip": True}
    )
    assert res_ip.allowed is False
    assert any("VIOLATION_NO_IP_CONCESSION" in v for v in res_ip.violations)

    # Violazione 2: Sconto eccessivo (15% vs max 10%)
    res_discount = DelegationEngine.evaluate_action(
        policy=policy,
        requested_action="send_commercial_proposal",
        financial_amount=10000.0,
        context_payload={"discount_percent": 15.0}
    )
    assert res_discount.allowed is False
    assert any("VIOLATION_MAX_DISCOUNT" in v for v in res_discount.violations)

    # Violazione 3: Soffitto finanziario superato (35.000€ vs 25.000€)
    res_finance = DelegationEngine.evaluate_action(
        policy=policy,
        requested_action="send_commercial_proposal",
        financial_amount=35000.0,
        context_payload={"discount_percent": 5.0}
    )
    assert res_finance.allowed is False
    assert any("FINANCIAL_CEILING_EXCEEDED" in v for v in res_finance.violations)

    # Violazione 4: Azione non delegata (es. 'modify_shareholder_agreement')
    res_unauth = DelegationEngine.evaluate_action(
        policy=policy,
        requested_action="modify_shareholder_agreement",
        financial_amount=1000.0,
        context_payload={}
    )
    assert res_unauth.allowed is False
    assert any("ACTION_NOT_DELEGATED" in v for v in res_unauth.violations)


def test_governance_gates_matrix():
    """Verifica l'instradamento delle classi di rischio A, B, C, D e il gate HITL."""
    role = Role(
        id="ROLE_OPERATOR",
        name="Operator",
        department_level="L2_TECH_SDLC",
        description="Standard execution role"
    )
    agent = Agent(
        id="agent-worker-01",
        name="Worker One",
        agent_type=AgentType.AI_SUBAGENT,
        assigned_roles=["ROLE_OPERATOR"],
        is_master=False
    )
    founder = Agent(
        id="agent-nunzio",
        name="Nunzio Lella",
        agent_type=AgentType.HUMAN,
        assigned_roles=["ROLE_FOUNDER_CEO"],
        is_master=True
    )

    # 1. Classe A: Auto-approve
    dec_a = GovernanceGateEvaluator.evaluate(
        actor=agent,
        role=role,
        risk_class=MutationRiskClass.CLASS_A_AUTO,
        action_name="update_notes"
    )
    assert dec_a.allowed_to_proceed is True
    assert dec_a.requires_human_approval is False
    assert dec_a.decision == GateDecisionType.APPROVED_AUTO

    # 2. Classe B: Auto-approve CON evidenza
    dec_b_ev = GovernanceGateEvaluator.evaluate(
        actor=agent,
        role=role,
        risk_class=MutationRiskClass.CLASS_B_EVIDENCE,
        has_verifiable_evidence=True,
        action_name="complete_task"
    )
    assert dec_b_ev.allowed_to_proceed is True
    assert dec_b_ev.requires_human_approval is False

    # 3. Classe B: Escalation HITL SENZA evidenza
    dec_b_no_ev = GovernanceGateEvaluator.evaluate(
        actor=agent,
        role=role,
        risk_class=MutationRiskClass.CLASS_B_EVIDENCE,
        has_verifiable_evidence=False,
        action_name="complete_task"
    )
    assert dec_b_no_ev.allowed_to_proceed is False
    assert dec_b_no_ev.requires_human_approval is True
    assert dec_b_no_ev.decision == GateDecisionType.ESCALATE_HITL

    # 4. Classe C: Richiede sempre HITL per agenti ordinari
    dec_c = GovernanceGateEvaluator.evaluate(
        actor=agent,
        role=role,
        risk_class=MutationRiskClass.CLASS_C_HITL,
        action_name="create_objective"
    )
    assert dec_c.allowed_to_proceed is False
    assert dec_c.requires_human_approval is True
    assert dec_c.decision == GateDecisionType.ESCALATE_HITL

    # 5. Classe D: Blocco per agente ordinario
    dec_d_blocked = GovernanceGateEvaluator.evaluate(
        actor=agent,
        role=role,
        risk_class=MutationRiskClass.CLASS_D_MASTER,
        action_name="alter_core_invariants"
    )
    assert dec_d_blocked.allowed_to_proceed is False
    assert dec_d_blocked.decision == GateDecisionType.BLOCKED_UNAUTHORIZED

    # 6. Classe D: Autorizzato per Master Assoluto (God Mode)
    dec_d_master = GovernanceGateEvaluator.evaluate(
        actor=founder,
        role=role,
        risk_class=MutationRiskClass.CLASS_D_MASTER,
        action_name="alter_core_invariants"
    )
    assert dec_d_master.allowed_to_proceed is True
    assert dec_d_master.decision == GateDecisionType.APPROVED_GOD_MODE


def test_virtual_memory_lens():
    """Verifica che le lenti di memoria virtuali aggreghino gli artefatti corretti senza duplicare file."""
    artifacts = [
        PersistentArtifactReference(
            id="art-1",
            canonical_id="QD-STR-001",
            domain=FunctionalDomain.D02_STRATEGY,
            authority=MemoryAuthority.CANONICAL_MEMORY,
            status=DocumentLifecycleStatus.APPROVED_CANONICAL,
            storage_path="02_STRATEGY/QD-STR-001.md",
            title="Strategic Core Qubitdata",
            created_by_agent_id="agent-nunzio",
            created_under_role_id="ROLE_FOUNDER_CEO",
            division_id="DIV_QUBITDATA"
        ),
        PersistentArtifactReference(
            id="art-2",
            canonical_id="QD-FIN-001",
            domain=FunctionalDomain.D04_ADMINISTRATION_FINANCE,
            authority=MemoryAuthority.CANONICAL_MEMORY,
            status=DocumentLifecycleStatus.APPROVED_CANONICAL,
            storage_path="04_ADMINISTRATION_FINANCE/QD-FIN-001.md",
            title="Consolidated Financial Debt Record",
            created_by_agent_id="agent-cfo",
            created_under_role_id="ROLE_CFO",
            division_id="DIV_QUBITDATA"
        ),
        PersistentArtifactReference(
            id="art-3",
            canonical_id="WP-01_CALL_0_DECISION",
            domain=FunctionalDomain.D10_OPERATIONS_RECORDS,
            authority=MemoryAuthority.DECISION_MEMORY,
            status=DocumentLifecycleStatus.OUTPUT,
            storage_path="10_OPERATIONS_RECORDS/WP-01/04_DECISIONS/dec_01.md",
            title="Decision on Strategic Restart",
            created_by_agent_id="agent-nunzio",
            created_under_role_id="ROLE_FOUNDER_CEO",
            division_id="DIV_QUBITDATA"
        ),
        PersistentArtifactReference(
            id="art-4",
            canonical_id="SYM-TEC-001",
            domain=FunctionalDomain.D05_TECHNOLOGY_DATA,
            authority=MemoryAuthority.CANONICAL_MEMORY,
            status=DocumentLifecycleStatus.APPROVED_CANONICAL,
            storage_path="05_TECHNOLOGY_DATA/SYM-TEC-001.md",
            title="Structura Core Architecture",
            created_by_agent_id="agent-antigravity",
            created_under_role_id="ROLE_TECH_LEAD",
            division_id="DIV_SYMBIOTIC_CORE"
        ),
    ]

    # 1. CFO Memory Lens (Qubitdata)
    cfo_view = VirtualMemoryLens.build_cfo_memory(artifacts, division_id="DIV_QUBITDATA")
    assert cfo_view.view_name == "CFO Memory View"
    assert len(cfo_view.canonical_documents) == 1
    assert cfo_view.canonical_documents[0].canonical_id == "QD-FIN-001"

    # 2. Technology & Product Lens (Symbiotic Core)
    tech_view = VirtualMemoryLens.build_tech_memory(artifacts, division_id="DIV_SYMBIOTIC_CORE")
    assert len(tech_view.canonical_documents) == 1
    assert tech_view.canonical_documents[0].canonical_id == "SYM-TEC-001"

    # 3. Vista globale Qubitdata
    qd_view = VirtualMemoryLens.build_view("Qubitdata Dossier", artifacts, division_id="DIV_QUBITDATA")
    assert len(qd_view.canonical_documents) == 2  # Strategy + Finance
    assert len(qd_view.decisions) == 1            # WP Decision
    assert qd_view.total_artifacts_count == 3
