"""Negative security contract tests.

These tests intentionally require private Org3 operations to reject anonymous
requests BEFORE any database access. Existing code may fail this contract;
that blocks a release until authentication and authorization are corrected.
"""
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from org3.api.main import app


@pytest.mark.parametrize(
    "method,path,payload",
    [
        ("get", "/v1/organizations", None),
        ("get", "/v1/organizations/example", None),
        ("get", "/v1/organizations/00000000-0000-0000-0000-000000000000/members", None),
        ("patch", "/v1/members/00000000-0000-0000-0000-000000000000", {"role": "OPERATOR"}),
        ("post", "/v1/organizations", {
            "slug": "anonymous-regression-" + uuid4().hex[:8],
            "name": "Should not be created",
            "owner_email": "nobody@example.invalid"
        }),
    ],
)
def test_private_operations_reject_anonymous_before_database(method, path, payload):
    with TestClient(app, raise_server_exceptions=False) as client:
        response = getattr(client, method)(path, json=payload) if payload is not None \
            else getattr(client, method)(path)
    assert response.status_code in (401, 403), (
        f"{method.upper()} {path}: expected 401/403 without a session, "
        f"received {response.status_code}; must not reach the database"
    )
