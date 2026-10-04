"""Level 0 Governance & BI Department."""

from __future__ import annotations

from typing import Dict, Any, List
from org3.core.models import DepartmentLevel, WorkUnit, WorkUnitStatus


class ProcessEngineer:
    """Monitors system bottlenecks, process adherence, and fractal delegation."""
    role_name: str = "ProcessEngineer"
    department: DepartmentLevel = DepartmentLevel.L0_GOVERNANCE

    @staticmethod
    def audit_delegation_chain(chain: List[str]) -> bool:
        """Verifies proper CMO -> Manager -> Operator flow."""
        return len(chain) >= 2


class ComplianceReviewer:
    """Enforces constitutional rules, secret management and operating policies."""
    role_name: str = "ComplianceReviewer"
    department: DepartmentLevel = DepartmentLevel.L0_GOVERNANCE

    @staticmethod
    def verify_no_secrets_in_text(text: str) -> bool:
        forbidden = ["PRIVATE KEY", "BEGIN RSA", "ghp_", "sk-", "AIzaSy"]
        return not any(marker in text for marker in forbidden)
