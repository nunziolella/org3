"""Unit tests for Org 3.0 Core and AICD Orchestrator."""

import tempfile
from pathlib import Path
from org3.core.models import WorkObject, WorkUnit, DepartmentLevel, WorkUnitStatus, GateStatus
from org3.core.gates import ZeroVulnerabilityGate, MergeGateValidator
from org3.orchestrator.aicd_orchestrator import AICDOrchestrator
from org3.departments.tech import CoderCell, QAValidatorCell
from org3.departments.governance import ComplianceReviewer, ProcessEngineer


def test_models_creation():
    unit = CoderCell.create_work_unit(
        unit_id="WU-001",
        title="Implement Feature X",
        specs="Detailed specs",
        acceptance_criteria=["Tests pass"]
    )
    assert unit.id == "WU-001"
    assert unit.department == DepartmentLevel.L2_TECH_SDLC
    assert unit.status == WorkUnitStatus.ASSIGNED

    wo = WorkObject(
        id="WO-001",
        project_id="PROJ-01",
        name="Build Module",
        description="Module description",
        work_units=[unit]
    )
    assert len(wo.work_units) == 1
    assert wo.work_units[0].assigned_role == "CoderCell"


def test_zero_vulnerability_clean():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "safe_module.py"
        test_file.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")

        result = ZeroVulnerabilityGate.scan_python_ast(tmpdir)
        assert result.status == GateStatus.PASSED
        assert len(result.findings) == 0


def test_zero_vulnerability_blocked():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "vuln_module.py"
        test_file.write_text("def run_code(code):\n    eval(code)\n", encoding="utf-8")

        result = ZeroVulnerabilityGate.scan_python_ast(tmpdir)
        assert result.status == GateStatus.BLOCKED
        assert any(f.issue_id == "RCE_EVAL" for f in result.findings)


def test_aicd_orchestrator_evaluation():
    with tempfile.TemporaryDirectory() as tmpdir:
        safe_file = Path(tmpdir) / "app.py"
        safe_file.write_text("print('hello')", encoding="utf-8")

        orchestrator = AICDOrchestrator(workspace_root=tmpdir)
        eval_res = orchestrator.evaluate_repository(tmpdir)
        assert eval_res["passed"] is True
        assert eval_res["overall_status"] == GateStatus.PASSED.value


def test_governance_and_qa_cells():
    assert ComplianceReviewer.verify_no_secrets_in_text("Regular string with no token") is True
    assert ComplianceReviewer.verify_no_secrets_in_text("My key is sk-123456789") is False

    assert ProcessEngineer.audit_delegation_chain(["CMO", "Manager", "Operator"]) is True
    assert ProcessEngineer.audit_delegation_chain(["OnlyOne"]) is False

    unit = CoderCell.create_work_unit("WU-002", "Fix", "Fix specs", [])
    assert QAValidatorCell.verify(unit, "4 passed in 0.2s") is True
    assert unit.status == WorkUnitStatus.APPROVED

    assert QAValidatorCell.verify(unit, "FAILED test_login") is False
    assert unit.status == WorkUnitStatus.REJECTED
