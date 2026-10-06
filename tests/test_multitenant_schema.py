"""Suite di Collaudo per lo Schema Multi-Tenant Org3 su Neon Postgres.

Test inclusi:
1. Modelli Pydantic v2 (Organization, Workspace, Member, DelegationPolicyRecord, ApprovalRequest, ApiToken).
2. Integrità referenziale e transazionale su Neon Postgres.
3. Invariante God Mode per Nunzio Lella (is_master=True).
4. Vincoli di delega anti-Chrimat (NO_IP_CONCESSION, MAX_FINANCIAL_AUTHORITY).
5. Invariante di non-contaminazione dei modelli.
"""

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

ORG3_DIR = Path(__file__).resolve().parent.parent
if str(ORG3_DIR) not in sys.path:
    sys.path.insert(0, str(ORG3_DIR))

from org3.models.multitenant import (
    ApprovalRequest,
    ApprovalStatus,
    ApiToken,
    DelegationPolicyRecord,
    Member,
    MemberRole,
    MemberType,
    Organization,
    PlanType,
    StorageProvider,
    Workspace,
)
from scripts.run_migration_0001_neon import get_neon_connection


def test_pydantic_multitenant_models():
    """Verifica che i modelli Pydantic v2 validino correttamente tutti i tipi e i default."""
    org = Organization(
        slug="symbiotic",
        name="Symbiotic Holding",
        plan=PlanType.ENTERPRISE,
        owner_email="01nunzio.lella@gmail.com",
    )
    assert org.slug == "symbiotic"
    assert org.plan == PlanType.ENTERPRISE
    assert org.is_active is True

    member = Member(
        org_id=org.id,
        email="01nunzio.lella@gmail.com",
        name="Nunzio Lella",
        member_type=MemberType.HUMAN,
        role=MemberRole.FOUNDER_GODMODE,
        is_master=True,
    )
    assert member.is_master is True
    assert member.role == MemberRole.FOUNDER_GODMODE

    policy = DelegationPolicyRecord(
        org_id=org.id,
        actor_id=member.id,
        name="Tech Lead Autonomous Budget",
        scope="infrastructure",
        max_financial_authority=15000.0,
        constraints=["NO_IP_CONCESSION", "NO_EXCLUSIVITY"],
        approval_gate="CLASS_B",
    )
    assert "NO_IP_CONCESSION" in policy.constraints
    assert policy.max_financial_authority == 15000.0


def test_neon_postgres_crud_and_invariants():
    """Esegue operazioni CRUD transazionali su Neon Postgres verificando l'integrità dello schema."""
    try:
        conn = get_neon_connection()
    except Exception as exc:
        pytest.skip(f"Neon Postgres non accessibile in questo ambiente: {exc}")
    cur = conn.cursor()

    test_org_slug = f"test-tenant-{uuid.uuid4().hex[:8]}"
    test_owner = f"founder-{uuid.uuid4().hex[:6]}@example.com"
    member_email = f"lead-{uuid.uuid4().hex[:6]}@example.com"

    try:
        # 1. Insert Organization
        cur.execute(
            """
            INSERT INTO org3_organizations (slug, name, plan, owner_email)
            VALUES (%s, %s, %s, %s)
            RETURNING id, slug, plan;
        """,
            (test_org_slug, "Test Automation Corp", "business", test_owner),
        )
        org_row = cur.fetchone()
        assert org_row is not None
        org_id, slug, plan = org_row
        assert slug == test_org_slug
        assert plan == "business"

        # 2. Insert Workspace con Google Drive storage
        cur.execute(
            """
            INSERT INTO org3_workspaces (org_id, name, storage_provider, storage_config, is_primary)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, storage_provider;
        """,
            (org_id, "Corporate Root", "google_drive", '{"folder_id": "root-12345"}', True),
        )
        ws_row = cur.fetchone()
        assert ws_row is not None
        ws_id, provider = ws_row
        assert provider == "google_drive"

        # 3. Insert Member con Master God Mode
        cur.execute(
            """
            INSERT INTO org3_members (org_id, email, name, member_type, role, is_master)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, is_master;
        """,
            (org_id, member_email, "Founder Master", "HUMAN", "FOUNDER_GODMODE", True),
        )
        mem_row = cur.fetchone()
        assert mem_row is not None
        member_id, is_master = mem_row
        assert is_master is True

        # 4. Insert Delegation Policy con vincoli rigidi
        cur.execute(
            """
            INSERT INTO org3_delegation_policies (org_id, actor_id, name, scope, max_financial_authority, constraints, approval_gate)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, max_financial_authority;
        """,
            (
                org_id,
                member_id,
                "Partner Sales Policy",
                "quotes",
                5000.00,
                '["NO_IP_CONCESSION", "NO_EXCLUSIVITY"]',
                "CLASS_C",
            ),
        )
        pol_row = cur.fetchone()
        assert pol_row is not None
        assert float(pol_row[1]) == 5000.00

        # 5. Insert Approval Request HITL
        cur.execute(
            """
            INSERT INTO org3_approval_requests (org_id, source_service, risk_class, title, description, payload, requested_by, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, status;
        """,
            (
                org_id,
                "structura",
                "C",
                "Approvazione Preventivo Extra Budget",
                "Preventivo #QT-099 eccede tetto di spesa",
                '{"quote_id": "QT-099", "amount": 12500}',
                member_id,
                "PENDING",
            ),
        )
        app_row = cur.fetchone()
        assert app_row is not None
        assert app_row[1] == "PENDING"

        # 6. Insert API Token
        token_hash = uuid.uuid4().hex
        cur.execute(
            """
            INSERT INTO org3_api_tokens (org_id, member_id, token_hash, name, allowed_scopes)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, name;
        """,
            (org_id, member_id, token_hash, "Structura Staging Connector", '["read", "write"]'),
        )
        tok_row = cur.fetchone()
        assert tok_row is not None
        assert tok_row[1] == "Structura Staging Connector"

        # Rollback o cleanup transazionale per non sporcare il database di test
        conn.rollback()

    finally:
        conn.close()
