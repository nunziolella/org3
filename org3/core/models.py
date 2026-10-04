"""Org 3.0 Core Models: Work Object, Work Unit, Department, Contract."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DepartmentLevel(str, Enum):
    L0_GOVERNANCE = "L0_GOVERNANCE"
    L1_STRATEGY_UX = "L1_STRATEGY_UX"
    L2_TECH_SDLC = "L2_TECH_SDLC"
    L3_MARKETING_GROWTH = "L3_MARKETING_GROWTH"
    L4_ADMIN_FINANCE = "L4_ADMIN_FINANCE"


class GateStatus(str, Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class WorkUnitStatus(str, Enum):
    DRAFT = "DRAFT"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    VALIDATING = "VALIDATING"
    APPROVED = "APPROVED"
    MERGED = "MERGED"
    REJECTED = "REJECTED"


class SecurityFinding(BaseModel):
    tool: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    issue_id: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None


class GateEvaluation(BaseModel):
    gate_name: str
    status: GateStatus
    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    findings: List[SecurityFinding] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)
    remediation_advice: Optional[str] = None


class WorkUnit(BaseModel):
    id: str
    title: str
    department: DepartmentLevel
    assigned_role: str
    status: WorkUnitStatus = WorkUnitStatus.DRAFT
    specifications: str
    acceptance_criteria: List[str] = Field(default_factory=list)
    gate_results: List[GateEvaluation] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class WorkObject(BaseModel):
    id: str
    project_id: str
    name: str
    description: str
    target_branch: str = "main"
    work_units: List[WorkUnit] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_locked: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
