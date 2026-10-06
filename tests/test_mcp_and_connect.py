"""Test suite for Step 5.5: Universal Multi-Tenant MCP Gateway, 'Connect to Org3' Protocol, and Notification Dispatch."""

import json
import uuid
import pytest
from fastapi.testclient import TestClient

from org3.api.main import app
from org3.notifications.dispatcher import NotificationDispatcher

client = TestClient(app)


def test_notification_dispatcher_formatting():
    dispatcher = NotificationDispatcher(
        org3_base_url="https://org3.godigix.com",
        cuprite_base_url="https://cuprite.godigix.com",
    )
    msg = dispatcher.format_approval_message(
        approval_id="appr-123",
        org_slug="qubitdata",
        org_name="Qubitdata SRL",
        title="Deploy Produzione Nuova Versione",
        description="Rollout del frontend su Cloudflare Pages",
        risk_class="C",
        source_service="structura",
        requested_by_name="Francesco PAI",
        financial_value=12500.0,
    )

    assert "⚠️ *ORG3 HITL APPROVAL REQUIRED* [Classe C]" in msg
    assert "Qubitdata SRL" in msg
    assert "€12,500.00" in msg
    assert "https://org3.godigix.com/app/?org=qubitdata#approvals" in msg
    assert "https://cuprite.godigix.com/app/approvals" in msg


def test_connect_to_org3_protocol_flow():
    try:
        from org3.api.db import get_connection
        _c = get_connection()
        _c.close()
    except Exception as exc:
        pytest.skip(f"Neon Postgres non accessibile per test di integrazione: {exc}")

    # 1. Crea Organizzazione con slug univoco
    slug = f"qubit-{uuid.uuid4().hex[:8]}"
    org_res = client.post(
        "/v1/organizations",
        json={
            "slug": slug,
            "name": "Qubitdata SRL",
            "owner_email": "francesco@qubitdata.it",
            "plan": "business",
        },
    )
    assert org_res.status_code == 201
    org_id = org_res.json()["id"]

    # 2. Crea Membro Master God Mode
    mem_res = client.post(
        f"/v1/organizations/{org_id}/members",
        json={
            "email": "01nunzio.lella@gmail.com",
            "name": "Nunzio Lella",
            "member_type": "HUMAN",
            "role": "FOUNDER_GODMODE",
            "is_master": True,
        },
    )
    assert mem_res.status_code == 201
    mem_id = mem_res.json()["id"]
    assert mem_res.json()["is_master"] is True

    # 3. Crea Workspace Storage
    ws_res = client.post(
        f"/v1/organizations/{org_id}/workspaces",
        json={
            "name": "Qubitdata Primary Drive",
            "storage_provider": "google_drive",
            "storage_config": {"root_folder_id": "gdrive_root_folder_123"},
            "is_primary": True,
        },
    )
    assert ws_res.status_code == 201

    # 4. Crea Delegation Policy (con vincolo CHRIMAT)
    pol_res = client.post(
        "/v1/delegation/policies",
        json={
            "org_id": org_id,
            "actor_id": mem_id,
            "name": "Commercial Authority",
            "scope": "commercial",
            "max_financial_authority": 50000.0,
            "constraints": ["NO_IP_CONCESSION", "NO_EXCLUSIVITY"],
            "approval_gate": "CLASS_C",
        },
    )
    assert pol_res.status_code == 201

    # 5. Genera Token API
    tok_res = client.post(
        "/v1/tokens",
        json={
            "org_id": org_id,
            "member_id": mem_id,
            "name": "Structura OS Production Token",
            "allowed_scopes": ["read", "write", "mcp"],
        },
    )
    assert tok_res.status_code == 201
    raw_token = tok_res.json()["token"]

    # 6. Test Connect Endpoint (/v1/connect)
    conn_res = client.post(
        "/v1/connect",
        json={
            "token": raw_token,
            "client_name": "Structura OS",
            "client_version": "3.3.0",
        },
    )
    assert conn_res.status_code == 200
    conn_data = conn_res.json()
    assert conn_data["status"] == "connected"
    assert conn_data["tier"] == "business"
    assert conn_data["tenant"]["slug"] == slug
    assert conn_data["member"]["is_master"] is True
    assert len(conn_data["workspaces"]) == 1
    assert len(conn_data["delegation_policies"]) == 1
    assert conn_data["features"]["multi_cloud_storage"] is True
    assert conn_data["features"]["god_mode_bypass"] is True

    # 7. Check status and manifest
    assert client.get("/v1/connect/status").status_code == 200
    assert client.get("/v1/connect/manifest").status_code == 200


def test_universal_mcp_gateway_lifecycle():
    try:
        from org3.api.db import get_connection
        _c = get_connection()
        _c.close()
    except Exception as exc:
        pytest.skip(f"Neon Postgres non accessibile per test di integrazione: {exc}")

    slug = f"symbiotic-{uuid.uuid4().hex[:8]}"
    # Setup Tenant & Member
    org_res = client.post(
        "/v1/organizations",
        json={
            "slug": slug,
            "name": "Symbiotic Holding",
            "owner_email": "01nunzio.lella@gmail.com",
            "plan": "enterprise",
        },
    )
    org_id = org_res.json()["id"]

    mem_res = client.post(
        f"/v1/organizations/{org_id}/members",
        json={
            "email": "01nunzio.lella@gmail.com",
            "name": "Nunzio Lella",
            "member_type": "HUMAN",
            "role": "FOUNDER_GODMODE",
            "is_master": True,
        },
    )
    mem_id = mem_res.json()["id"]

    # Add workspace
    client.post(
        f"/v1/organizations/{org_id}/workspaces",
        json={
            "name": "Local Test Workspace",
            "storage_provider": "local_fs",
            "storage_config": {"base_path": "./test_fs"},
            "is_primary": True,
        },
    )

    # Token
    tok_res = client.post(
        "/v1/tokens",
        json={
            "org_id": org_id,
            "member_id": mem_id,
            "name": "Cursor IDE MCP Token",
            "allowed_scopes": ["mcp"],
        },
    )
    raw_token = tok_res.json()["token"]

    headers = {"Authorization": f"Bearer {raw_token}"}

    # 1. MCP initialize
    init_res = client.post(
        f"/v1/mcp/{slug}",
        headers=headers,
        json={"jsonrpc": "2.0", "id": 1, "method": "initialize"},
    )
    assert init_res.status_code == 200
    init_data = init_res.json()
    assert init_data["result"]["serverInfo"]["name"] == "org3-universal-mcp"
    assert init_data["result"]["serverInfo"]["tenant"] == slug

    # 2. MCP tools/list
    tools_res = client.post(
        f"/v1/mcp/{slug}",
        headers=headers,
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    )
    assert tools_res.status_code == 200
    tools = tools_res.json()["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "org3_list_domains" in tool_names
    assert "org3_get_identity" in tool_names
    assert "org3_evaluate_action" in tool_names
    assert "org3_request_approval" in tool_names

    # 3. Call org3_list_domains
    call_dom = client.post(
        f"/v1/mcp/{slug}",
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "org3_list_domains", "arguments": {}},
        },
    )
    assert call_dom.status_code == 200
    dom_text = call_dom.json()["result"]["content"][0]["text"]
    dom_obj = json.loads(dom_text)
    assert len(dom_obj["domains"]) == 12 or len(dom_obj["domains"]) >= 10

    # 4. Call org3_get_identity
    call_id = client.post(
        f"/v1/mcp/{slug}",
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "org3_get_identity", "arguments": {}},
        },
    )
    assert call_id.status_code == 200
    id_obj = json.loads(call_id.json()["result"]["content"][0]["text"])
    assert id_obj["tenant"]["slug"] == slug
    assert id_obj["member"]["is_master"] is True

    # 5. Call org3_evaluate_action
    call_eval = client.post(
        f"/v1/mcp/{slug}",
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "org3_evaluate_action",
                "arguments": {
                    "action": "deploy.infrastructure",
                    "financial_impact": 1500.0,
                    "parameters": {"environment": "production"},
                },
            },
        },
    )
    assert call_eval.status_code == 200
    eval_obj = json.loads(call_eval.json()["result"]["content"][0]["text"])
    assert eval_obj["authorized"] is True  # Master Assoluto bypass

    # 6. Call org3_request_approval (HITL alert)
    call_req = client.post(
        f"/v1/mcp/{slug}",
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "org3_request_approval",
                "arguments": {
                    "title": "Richiesta Licenza Cloud Run Scale-up",
                    "description": "Necessario incremento memoria a 8GB per ingestione Memograph",
                    "risk_class": "C",
                    "payload": {"amount": 250.0},
                },
            },
        },
    )
    assert call_req.status_code == 200
    req_obj = json.loads(call_req.json()["result"]["content"][0]["text"])
    appr_id = req_obj["approval_id"]
    assert req_obj["status"] == "PENDING"
    assert req_obj["notification_dispatched"] is True
    assert f"https://org3.godigix.com/app/?org={slug}#approvals" in req_obj["deep_link"]

    # 7. Call org3_list_pending_approvals
    call_list = client.post(
        f"/v1/mcp/{slug}",
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {"name": "org3_list_pending_approvals", "arguments": {}},
        },
    )
    assert call_list.status_code == 200
    list_obj = json.loads(call_list.json()["result"]["content"][0]["text"])
    assert len(list_obj["pending_approvals"]) == 1

    # 8. Call org3_resolve_approval
    call_res = client.post(
        f"/v1/mcp/{slug}",
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {
                "name": "org3_resolve_approval",
                "arguments": {
                    "approval_id": appr_id,
                    "action": "APPROVED",
                    "resolution_note": "Approvato da Master Assoluto via MCP",
                },
            },
        },
    )
    assert call_res.status_code == 200
    res_obj = json.loads(call_res.json()["result"]["content"][0]["text"])
    assert res_obj["status"] == "APPROVED"
