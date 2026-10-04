"""AICD Orchestrator: Cognitive Continuous Integration and Delivery Engine."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from org3.core.gates import MergeGateValidator, ZeroVulnerabilityGate
from org3.core.models import GateEvaluation, GateStatus, WorkObject, WorkUnit

log = logging.getLogger("org3.aicd")


class AICDOrchestrator:
    """Cognitive CI/CD pipeline orchestrator that tests, validates, and manages gates."""

    def __init__(self, workspace_root: Optional[str | Path] = None):
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()

    def evaluate_repository(self, target_dir: str | Path) -> Dict[str, Any]:
        """Runs the full battery of gates on a repository path."""
        target_path = Path(target_dir)
        log.info("Running AICD evaluation on: %s", target_path)

        # 1. Zero-Vulnerability Security Gate
        security_eval = ZeroVulnerabilityGate.scan_python_ast(target_path)

        # 2. Merge Gate Verification
        merge_eval = MergeGateValidator.validate_merge_readiness(target_path)

        is_green = (
            security_eval.status == GateStatus.PASSED and
            merge_eval.status == GateStatus.PASSED
        )

        return {
            "target_path": str(target_path),
            "passed": is_green,
            "overall_status": GateStatus.PASSED.value if is_green else GateStatus.BLOCKED.value,
            "gates": {
                "security_ast": security_eval.model_dump(),
                "merge_readiness": merge_eval.model_dump()
            },
            "summary": "Repository is compliant with Zero-Vulnerability & Merge Gate criteria." if is_green else "Violations detected. Review findings before proceed."
        }

    def process_work_object(self, work_object: WorkObject) -> WorkObject:
        """Evaluates all units in a WorkObject and updates their gate states."""
        for unit in work_object.work_units:
            eval_res = MergeGateValidator.validate_merge_readiness(self.workspace_root)
            unit.gate_results.append(eval_res)
            if eval_res.status == GateStatus.PASSED:
                unit.status = "APPROVED"
            else:
                unit.status = "VALIDATING"
        return work_object
