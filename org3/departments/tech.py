"""Level 2 Tech Department: CoderCell, QAValidatorCell, ArchitectCell."""

from __future__ import annotations

from typing import Dict, Any, List
from org3.core.models import DepartmentLevel, WorkUnit, WorkUnitStatus


class CoderCell:
    """Automated coding cell for scoped feature implementation."""
    role_name: str = "CoderCell"
    department: DepartmentLevel = DepartmentLevel.L2_TECH_SDLC

    @staticmethod
    def create_work_unit(unit_id: str, title: str, specs: str, acceptance_criteria: List[str]) -> WorkUnit:
        return WorkUnit(
            id=unit_id,
            title=title,
            department=DepartmentLevel.L2_TECH_SDLC,
            assigned_role="CoderCell",
            status=WorkUnitStatus.ASSIGNED,
            specifications=specs,
            acceptance_criteria=acceptance_criteria
        )


class QAValidatorCell:
    """Independent quality assurance and test validation agent."""
    role_name: str = "QAValidatorCell"
    department: DepartmentLevel = DepartmentLevel.L2_TECH_SDLC

    @staticmethod
    def verify(work_unit: WorkUnit, test_output: str) -> bool:
        passed = "FAIL" not in test_output.upper() and "ERROR" not in test_output.upper()
        if passed:
            work_unit.status = WorkUnitStatus.APPROVED
        else:
            work_unit.status = WorkUnitStatus.REJECTED
        return passed
