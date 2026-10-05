"""Suite di Collaudo E2E per le REST API di Org3 Platform.

Testa in modo completo tutti gli endpoint di:
- Health check
- Organizations & Workspaces
- Members & IAM (inclusa invariante God Mode)
- Delegation Policies & Real-Time Evaluation Engine
- Approvals & HITL Hub
- Org3 Connect Tokens & Validation
"""

import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ORG3_DIR = Path(__file__).resolve().parent.parent
if str(ORG3_DIR) not in sys.path:
    sys.path.insert(0, str(ORG3_DIR))

from org3.api.main import app

client = TestClient(app)


def test_health_check():
    """Verifica l'endpoint di sanità del microservizio Org3 Platform."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "org3-platform-api"
    assert data["version"] == "3.3.0"


def test_full_organization_delegation_and_token_flow():
    """Esegue il ciclo di vita completo di un'organizzazione cliente su Org3:
    1. Onboarding Organizzazione.
    2. Creazione Workspace Google Drive.
    3. Censimento Membri (Founder Master + Partner Commerciale).
    4. Creazione Contratto di Delega anti-Chrimat.
    5. Valutazione Delega Real-Time (Azione autorizzata, Azione che tocca IP bloccata, Sforamento budget).
    6. Flusso Approvazione HITL (Invio richiesta ed esito).
    7. Emissione e Validazione Token Org3 Connect.
    """
    # 1. Onboarding Organizzazione
    unique_slug = f"pilot-{uuid.uuid4().hex[:8]}"
    create_org_res = client.post(
        "/v1/organizations",
        json={
            "slug": unique_slug,
            "name": "Pilot Innovation Labs",
            "owner_email": "01nunzio.lella@gmail.com",
            "plan": "business",
        },
    )
    assert create_org_res.status_code == 201
    org_data = create_org_res.json()
    org_id = org_data["id"]
    assert org_data["slug"] == unique_slug
    assert org_data["plan"] == "business"

    # Recupero per slug
    get_org_res = client.get(f"/v1/organizations/{unique_slug}")
    assert get_org_res.status_code == 200
    assert get_org_res.json()["id"] == org_id

    # 2. Creazione Workspace Google Drive
    ws_res = client.post(
        f"/v1/organizations/{org_id}/workspaces",
        json={
            "name": "Corporate Shared Drive",
            "storage_provider": "google_drive",
            "storage_config": {"folder_id": "gdrive_shared_root_001"},
            "is_primary": True,
        },
    )
    assert ws_res.status_code == 201
    assert ws_res.json()["storage_provider"] == "google_drive"

    # 3. Censimento Membri
    # Founder Master (Nunzio Lella)
    founder_res = client.post(
        f"/v1/organizations/{org_id}/members",
        json={
            "email": "01nunzio.lella@gmail.com",
            "name": "Nunzio Lella",
            "member_type": "HUMAN",
            "role": "FOUNDER_GODMODE",
            "is_master": True,
        },
    )
    assert founder_res.status_code == 201
    founder_id = founder_res.json()["id"]
    assert founder_res.json()["is_master"] is True

    # Partner / Sales Agent (Francesco)
    partner_email = f"francesco-{uuid.uuid4().hex[:6]}@example.com"
    partner_res = client.post(
        f"/v1/organizations/{org_id}/members",
        json={
            "email": partner_email,
            "name": "Francesco Partner",
            "member_type": "HUMAN",
            "role": "OPERATOR",
            "is_master": False,
        },
    )
    assert partner_res.status_code == 201
    partner_id = partner_res.json()["id"]
    assert partner_res.json()["is_master"] is False

    # 4. Creazione Contratto di Delega anti-Chrimat per Francesco
    policy_res = client.post(
        "/v1/delegation/policies",
        json={
            "org_id": org_id,
            "actor_id": partner_id,
            "name": "Commercial Negotiation Policy",
            "scope": "commercial_quote",
            "max_financial_authority": 5000.0,
            "constraints": ["NO_IP_CONCESSION", "NO_EXCLUSIVITY", "NO_ROADMAP_COMMITMENT"],
            "approval_gate": "CLASS_C",
        },
    )
    assert policy_res.status_code == 201
    policy_id = policy_res.json()["id"]
    assert policy_res.json()["max_financial_authority"] == 5000.0

    # 5. Valutazione Delega Real-Time (POST /v1/delegation/evaluate)
    # Test A: Offerta commerciale standard entro 5.000€ -> AUTORIZZATA
    eval_ok = client.post(
        "/v1/delegation/evaluate",
        json={
            "org_id": org_id,
            "actor_id": partner_id,
            "action": "commercial_quote.create",
            "requested_amount": 3500.0,
            "touches_ip": False,
            "grants_exclusivity": False,
            "commits_roadmap": False,
        },
    )
    assert eval_ok.status_code == 200
    res_a = eval_ok.json()
    assert res_a["allowed"] is True
    assert len(res_a["violations"]) == 0

    # Test B: Tentativo di cessione IP (Caso CHRIMAT) -> BLOCCATO da vincolo stringente
    eval_ip = client.post(
        "/v1/delegation/evaluate",
        json={
            "org_id": org_id,
            "actor_id": partner_id,
            "action": "commercial_quote.create",
            "requested_amount": 3500.0,
            "touches_ip": True,  # Attenzione! Cessione IP
            "grants_exclusivity": False,
            "commits_roadmap": False,
        },
    )
    assert eval_ip.status_code == 200
    res_b = eval_ip.json()
    assert res_b["allowed"] is False
    assert any("IP" in v for v in res_b["violations"])

    # Test C: Importo oltre soglia (12.000€ > 5.000€) -> BLOCCATO da soffitto economico
    eval_amt = client.post(
        "/v1/delegation/evaluate",
        json={
            "org_id": org_id,
            "actor_id": partner_id,
            "action": "commercial_quote.create",
            "requested_amount": 12000.0,
            "touches_ip": False,
        },
    )
    assert eval_amt.status_code == 200
    res_c = eval_amt.json()
    assert res_c["allowed"] is False
    assert res_c["requires_hitl"] is True

    # Test D: Nunzio (God Mode) esegue qualsiasi azione -> SEMPRE AUTORIZZATO
    eval_god = client.post(
        "/v1/delegation/evaluate",
        json={
            "org_id": org_id,
            "actor_id": founder_id,
            "action": "strategic_acquisition",
            "requested_amount": 500000.0,
            "touches_ip": True,
            "grants_exclusivity": True,
        },
    )
    assert eval_god.status_code == 200
    res_d = eval_god.json()
    assert res_d["allowed"] is True
    assert "God Mode" in res_d["reason"]

    # 6. Flusso Approvazioni HITL
    req_hitl = client.post(
        "/v1/approvals/request",
        json={
            "org_id": org_id,
            "source_service": "structura",
            "risk_class": "C",
            "title": "Richiesta Approvazione Preventivo Extra Budget",
            "description": "Preventivo 12.000€ per cliente speciale",
            "payload": {"amount": 12000.0, "client": "Acme Corp"},
            "requested_by": partner_id,
        },
    )
    assert req_hitl.status_code == 201
    approval_id = req_hitl.json()["id"]
    assert req_hitl.json()["status"] == "PENDING"

    # Risoluzione HITL da parte del Founder
    resolve_res = client.post(
        f"/v1/approvals/{approval_id}/resolve",
        json={
            "action": "APPROVED",
            "resolution_note": "Autorizzato sconto per trattativa strategica",
            "resolved_by": founder_id,
        },
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "APPROVED"
    assert resolve_res.json()["resolved_by"] == founder_id

    # 7. Emissione e Validazione Token Org3 Connect
    token_res = client.post(
        "/v1/tokens",
        json={
            "org_id": org_id,
            "member_id": founder_id,
            "name": "Structura OS Cuprite Connector",
            "allowed_scopes": ["read", "write", "governance"],
        },
    )
    assert token_res.status_code == 201
    raw_api_key = token_res.json()["token"]
    assert raw_api_key.startswith("org3_sk_")

    # Validazione token (chiamata simulata da Structura / cuprite.godigix.com)
    val_res = client.post(
        "/v1/tokens/validate",
        json={"token": raw_api_key},
    )
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["valid"] is True
    assert val_data["org_slug"] == unique_slug
    assert val_data["member_email"] == "01nunzio.lella@gmail.com"
    assert val_data["is_master"] is True
