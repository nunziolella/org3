"""Org 3.0 Command Line Interface."""

import json
import sys
from pathlib import Path
from org3.orchestrator.aicd_orchestrator import AICDOrchestrator
from org3.core.ontology import FunctionalDomain, MemoryAuthority
from org3.core.delegation import (
    DelegationPolicy,
    DelegationConstraint,
    DelegationConstraintType,
    DelegationEngine,
)
from org3.core.governance_gates import (
    MutationRiskClass,
    GovernanceGateEvaluator,
)


def main():
    if len(sys.argv) < 2:
        print("Org 3.0 CLI — Usage: org3 <command> [args]")
        print("Commands:")
        print("  aicd-validate <path>       Run AST security & merge gates on path")
        print("  audit-security <path>      Run AST security scan only")
        print("  list-domains               List the 10 canonical persistent information domains")
        print("  test-chrimat-delegation    Run a self-test of the CHRIMAT delegation policy")
        sys.exit(0)

    cmd = sys.argv[1]
    target = sys.argv[2] if len(sys.argv) > 2 else "."
    orchestrator = AICDOrchestrator()

    if cmd in ("aicd-validate", "audit-security", "gate-check"):
        result = orchestrator.evaluate_repository(target)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["passed"] else 1)

    elif cmd == "list-domains":
        domains = [d.value for d in FunctionalDomain]
        authorities = [a.value for a in MemoryAuthority]
        print(json.dumps({"functional_domains": domains, "memory_authorities": authorities}, indent=2))
        sys.exit(0)

    elif cmd == "test-chrimat-delegation":
        # Demo / test live del caso CHRIMAT
        policy = DelegationPolicy(
            id="del-chrimat-001",
            delegator_id="agent-nunzio",
            delegate_id="agent-francesco",
            allowed_actions=["send_commercial_proposal", "negotiate_contract"],
            scope="partner:chrimat",
            constraints=[
                DelegationConstraint(constraint_type=DelegationConstraintType.NO_IP_CONCESSION),
                DelegationConstraint(constraint_type=DelegationConstraintType.NO_EXCLUSIVITY),
                DelegationConstraint(constraint_type=DelegationConstraintType.NO_ROADMAP_COMMITMENT),
                DelegationConstraint(constraint_type=DelegationConstraintType.MAX_DISCOUNT_PERCENT, value=10.0),
            ],
            financial_ceiling=25000.0,
            requires_hitl_escalation=False,
        )

        # Caso violazione IP
        test_payload = {"concedes_ip": True, "discount_percent": 5.0}
        eval_res = DelegationEngine.evaluate_action(
            policy=policy,
            requested_action="send_commercial_proposal",
            financial_amount=15000.0,
            context_payload=test_payload,
        )
        print("Test CHRIMAT (Violazione IP bloccata):")
        print(json.dumps(eval_res.model_dump(), indent=2))
        sys.exit(0 if not eval_res.allowed else 1)

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
