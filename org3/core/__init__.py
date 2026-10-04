"""Org 3.0 Core Package: Models, Ontology, Delegation, Views and Gates."""

from org3.core.models import (
    DepartmentLevel,
    GateStatus,
    WorkUnitStatus,
    SecurityFinding,
    GateEvaluation,
    WorkUnit,
    WorkObject,
)
from org3.core.ontology import (
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
)
from org3.core.delegation import (
    DelegationConstraintType,
    DelegationConstraint,
    DelegationPolicy,
    DelegationEvaluationResult,
    DelegationEngine,
)
from org3.core.views import (
    VirtualMemoryView,
    VirtualMemoryLens,
)
from org3.core.governance_gates import (
    MutationRiskClass,
    GateDecisionType,
    GovernanceGateDecision,
    GovernanceGateEvaluator,
)
from org3.core.gates import (
    ZeroVulnerabilityGate,
    MergeGateValidator,
)

__all__ = [
    # Legacy & AICD
    "DepartmentLevel",
    "GateStatus",
    "WorkUnitStatus",
    "SecurityFinding",
    "GateEvaluation",
    "WorkUnit",
    "WorkObject",
    "ZeroVulnerabilityGate",
    "MergeGateValidator",
    # Ontology & Persistent Info Layer
    "FunctionalDomain",
    "MemoryAuthority",
    "DocumentLifecycleStatus",
    "OrgStructureType",
    "AgentType",
    "ActionPermission",
    "Role",
    "Agent",
    "Division",
    "OrganizationalUnit",
    "PersistentArtifactReference",
    # Delegation (CHRIMAT solution)
    "DelegationConstraintType",
    "DelegationConstraint",
    "DelegationPolicy",
    "DelegationEvaluationResult",
    "DelegationEngine",
    # Views & Lenses
    "VirtualMemoryView",
    "VirtualMemoryLens",
    # Governance Gates
    "MutationRiskClass",
    "GateDecisionType",
    "GovernanceGateDecision",
    "GovernanceGateEvaluator",
]
