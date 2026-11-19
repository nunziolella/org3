"""Regression tests: release guards must BLOCK missing or failed evidence."""
import json
import sys
from pathlib import Path

import pytest

from org3.security.release_gate import REQUIRED_CHECKS, GateError, evaluate, read_policy


def make_policy(path: Path, command=None):
    command = command or [sys.executable, "-c", "pass"]
    path.write_text(json.dumps({
        "schema_version": 1,
        "checks": [{"id": key, "command": command, "timeout_seconds": 10}
                   for key in REQUIRED_CHECKS],
    }), encoding="utf-8")
    return path


def test_valid_evidence_passes(tmp_path, monkeypatch):
    monkeypatch.setattr("org3.security.release_gate.git_sha", lambda repo: "a" * 40)
    report = evaluate(tmp_path, make_policy(tmp_path / "policy.json"), "a" * 40)
    assert report["status"] == "PASSED"
    assert len(report["checks"]) == 6
    assert report["commit_sha"] == "a" * 40


def test_failed_command_blocks(tmp_path, monkeypatch):
    monkeypatch.setattr("org3.security.release_gate.git_sha", lambda repo: "a" * 40)
    policy = make_policy(tmp_path / "policy.json",
                         [sys.executable, "-c", "raise SystemExit(2)"])
    report = evaluate(tmp_path, policy)
    assert report["status"] == "BLOCKED"
    assert all(c["status"] == "BLOCKED" for c in report["checks"])


def test_unavailable_tool_blocks(tmp_path, monkeypatch):
    monkeypatch.setattr("org3.security.release_gate.git_sha", lambda repo: "a" * 40)
    policy = make_policy(tmp_path / "policy.json",
                         ["__org3_command_that_does_not_exist__"])
    report = evaluate(tmp_path, policy)
    assert report["status"] == "BLOCKED"
    assert all(c["reason"] == "tool_unavailable" for c in report["checks"])


def test_missing_check_is_invalid(tmp_path):
    path = make_policy(tmp_path / "policy.json")
    policy = json.loads(path.read_text())
    policy["checks"].pop()
    path.write_text(json.dumps(policy))
    with pytest.raises(GateError):
        read_policy(path)


def test_duplicate_check_is_invalid(tmp_path):
    path = make_policy(tmp_path / "policy.json")
    policy = json.loads(path.read_text())
    policy["checks"].append(policy["checks"][0])
    path.write_text(json.dumps(policy))
    with pytest.raises(GateError):
        read_policy(path)


def test_untrusted_shell_string_is_invalid(tmp_path):
    path = make_policy(tmp_path / "policy.json")
    policy = json.loads(path.read_text())
    policy["checks"][0]["command"] = "echo pass; true"
    path.write_text(json.dumps(policy))
    with pytest.raises(GateError):
        read_policy(path)


def test_mismatched_sha_blocks(tmp_path, monkeypatch):
    monkeypatch.setattr("org3.security.release_gate.git_sha", lambda repo: "a" * 40)
    with pytest.raises(GateError):
        evaluate(tmp_path, make_policy(tmp_path / "policy.json"), "b" * 40)


def test_missing_policy_blocks(tmp_path, monkeypatch):
    monkeypatch.setattr("org3.security.release_gate.git_sha", lambda repo: "a" * 40)
    with pytest.raises(GateError):
        evaluate(tmp_path, tmp_path / "missing.json")


def test_no_raw_tool_output_in_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr("org3.security.release_gate.git_sha", lambda repo: "a" * 40)
    secret = "DO_NOT_EMIT_SECRET"
    policy = make_policy(tmp_path / "policy.json",
        [sys.executable, "-c", f"print('{secret}')"])
    report = evaluate(tmp_path, policy)
    assert secret not in json.dumps(report)
