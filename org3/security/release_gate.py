"""Fail-closed, policy-driven release gate for ORG3.

A gate result is evidence for a particular checkout, NOT a security guarantee.
The policy must be supplied by a trusted control-plane checkout, not from an
untrusted pull request. Never run this tool with production credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_CHECKS = (
    "static-analysis",
    "secrets",
    "dependencies",
    "tests",
    "authorization",
    "build",
)
MAX_TIMEOUT_SECONDS = 900


class GateError(ValueError):
    """Invalid policy or missing verification evidence."""


def read_policy(path: Path) -> tuple[dict, str]:
    try:
        raw = path.read_bytes()
        data = json.loads(raw)
    except (OSError, ValueError) as exc:
        raise GateError(f"Unable to load trusted policy: {type(exc).__name__}") from exc

    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise GateError("A policy object with schema_version=1 is required")
    checks = data.get("checks")
    if not isinstance(checks, list) or len(checks) < len(REQUIRED_CHECKS):
        raise GateError("All six mandatory check categories must be present")
    ids = [check.get("id") if isinstance(check, dict) else None for check in checks]
    if len(set(ids)) != len(ids) or not set(REQUIRED_CHECKS).issubset(ids):
        raise GateError("Required checks missing, invalid, or duplicated")

    for check in checks:
        command = check.get("command")
        timeout = check.get("timeout_seconds", 300)
        if (
            not isinstance(check.get("id"), str)
            or not isinstance(command, list)
            or not command
            or not all(isinstance(arg, str) and arg for arg in command)
            or not isinstance(timeout, int)
            or isinstance(timeout, bool)
            or not 1 <= timeout <= MAX_TIMEOUT_SECONDS
        ):
            raise GateError(f"Invalid command/timeout for check: {check.get('id')}")
        if any("\x00" in arg for arg in command):
            raise GateError("NUL byte in command argument")
    return data, hashlib.sha256(raw).hexdigest()


def git_sha(repo: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=repo, capture_output=True, text=True, timeout=15, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GateError("Cannot verify repository commit") from exc
    sha = result.stdout.strip()
    if result.returncode or len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
        raise GateError("Repository has no verifiable Git commit")
    return sha


def evaluate(repo: Path, policy: Path, expected_sha: str | None = None) -> dict:
    """Evaluate all checks. Errors, timeouts and missing tools BLOCK."""
    if not repo.is_dir():
        raise GateError("Repository directory not found")
    commit = git_sha(repo)
    if expected_sha and expected_sha != commit:
        raise GateError("Checkout SHA does not match the requested release SHA")
    document, policy_sha256 = read_policy(policy)
    results = []
    env = dict(os.environ)
    env["CI"] = "true"
    env["GIT_TERMINAL_PROMPT"] = "0"
    for check in document["checks"]:
        name = check["id"]
        try:
            result = subprocess.run(
                check["command"], cwd=repo, env=env,
                capture_output=True, timeout=check.get("timeout_seconds", 300),
                check=False,
            )
            state = "PASSED" if result.returncode == 0 else "BLOCKED"
            record = {"id": name, "status": state, "exit_code": result.returncode}
        except subprocess.TimeoutExpired:
            record = {"id": name, "status": "BLOCKED", "reason": "timeout"}
        except OSError:
            record = {"id": name, "status": "BLOCKED", "reason": "tool_unavailable"}
        # Deliberately never include raw command output: it can contain secrets.
        results.append(record)
        print(f"[ORG3] {name}: {record['status']}", flush=True)
    passed = all(check["status"] == "PASSED" for check in results)
    return {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "commit_sha": commit,
        "policy_sha256": policy_sha256,
        "status": "PASSED" if passed else "BLOCKED",
        "checks": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ORG3 security release gate")
    parser.add_argument("--repository", required=True)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--expected-sha")
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    try:
        report = evaluate(
            Path(args.repository).resolve(),
            Path(args.policy).resolve(),
            args.expected_sha,
        )
    except (GateError, Exception) as exc:
        # Fail closed even if the policy, checkout or runner is unavailable.
        report = {"schema_version": 1, "status": "BLOCKED",
                  "reason": f"gate_error:{type(exc).__name__}"}
    try:
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except OSError:
        print("[ORG3] BLOCKED: could not persist gate evidence", file=sys.stderr)
        return 1
    print(f"[ORG3] RELEASE {report['status']}")
    return 0 if report["status"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
