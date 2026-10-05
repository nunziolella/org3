"""Comprehensive Test Suite for Org3 Multi-Cloud Storage Adapters & Anti-Quota Shield.

Verifica:
1. Ontologia 10 Domini Persistenti e normalizzazione chiavi.
2. StorageCacheEngine: hit/miss, TTL, shield anti-quota e backoff 429.
3. LocalStorageAdapter: mapping, I/O, hashing SHA256, invalidazione cache.
4. GoogleDriveStorageAdapter: simulazione gerarchia, campi leggeri, anti-quota.
5. S3StorageAdapter: partizione chiavi per dominio, simulazione, hashing.
6. StorageAdapterFactory: risoluzione dinamica e singleton per workspace.
7. FastAPI REST API endpoints: upload, list, fingerprint, content download, cache invalidation.
"""

from __future__ import annotations

import asyncio
import base64
import os
import shutil
import tempfile
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from org3.api.main import app
from org3.models.multitenant import PlanType, StorageProvider
from org3.storage.base import (
    CANONICAL_DOMAINS,
    DomainFolderMap,
    StorageItem,
    normalize_domain_key,
)
from org3.storage.cache import StorageCacheEngine
from org3.storage.factory import StorageAdapterFactory
from org3.storage.gdrive import GoogleDriveStorageAdapter
from org3.storage.local import LocalStorageAdapter
from org3.storage.s3 import S3StorageAdapter


client = TestClient(app)


def test_canonical_domains_and_normalization():
    """Verifica che i 10 domini persistenti (+ 00 e 99) siano definiti e normalizzati correttamente."""
    assert len(CANONICAL_DOMAINS) == 12
    assert "01_CORPORATE" in CANONICAL_DOMAINS
    assert "02_FINANCE_LEGAL" in CANONICAL_DOMAINS
    assert "06_PRODUCT_RESEARCH" in CANONICAL_DOMAINS
    assert "10_OPERATIONS_RECORDS" in CANONICAL_DOMAINS

    # Test normalizzazione
    assert normalize_domain_key("01") == "01_CORPORATE"
    assert normalize_domain_key("1") == "01_CORPORATE"
    assert normalize_domain_key("01_CORPORATE") == "01_CORPORATE"
    assert normalize_domain_key("corporate") == "01_CORPORATE"
    assert normalize_domain_key("finance") == "02_FINANCE_LEGAL"
    assert normalize_domain_key("legal") == "02_FINANCE_LEGAL"
    assert normalize_domain_key("product") == "06_PRODUCT_RESEARCH"
    assert normalize_domain_key("engineering") == "07_ENGINEERING_INFRA"
    assert normalize_domain_key("brand") == "08_ASSETS_BRAND"
    assert normalize_domain_key("memory") == "09_MANAGEMENT_MEMORY"
    assert normalize_domain_key("ledger") == "10_OPERATIONS_RECORDS"
    assert normalize_domain_key("unknown_keyword_xyz") == "10_OPERATIONS_RECORDS"


def test_storage_cache_engine_and_anti_quota():
    """Verifica il comportamento del cache engine, TTL e metriche anti-quota."""
    cache = StorageCacheEngine(default_ttl_seconds=0.5, rate_limit_threshold_per_window=3)
    ws_id = "ws_test_cache"

    # 1. Miss iniziale
    val = cache.get(ws_id, "list", "01_CORPORATE")
    assert val is None
    stats = cache.get_stats()
    assert stats["misses"] == 1
    assert stats["hits"] == 0

    # 2. Set e Hit
    cache.set(ws_id, "list", "01_CORPORATE", ["item1", "item2"])
    val2 = cache.get(ws_id, "list", "01_CORPORATE")
    assert val2 == ["item1", "item2"]
    stats2 = cache.get_stats()
    assert stats2["hits"] == 1

    # 3. Invalidation
    cache.invalidate(ws_id, "list")
    assert cache.get(ws_id, "list", "01_CORPORATE") is None

    # 4. Stress Rate Limit & Grace Period
    for _ in range(4):
        cache.record_external_call(ws_id)
    assert cache.is_rate_limit_stressed(ws_id) is True

    # 5. Retry con backoff su 429
    attempts = 0

    async def flaky_call():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RuntimeError("HTTP 429 Too Many Requests: Rate limit exceeded")
        return "success_recovered"

    result = asyncio.run(
        cache.execute_with_anti_quota_retry(
            ws_id,
            "flaky_call",
            flaky_call,
            max_retries=3,
            base_delay_seconds=0.01,
        )
    )
    assert result == "success_recovered"
    assert attempts == 3
    assert cache.get_stats()["anti_quota_saves"] >= 2


def test_local_storage_adapter():
    """Verifica il ciclo di vita completo del LocalStorageAdapter su filesystem temporaneo."""
    temp_dir = tempfile.mkdtemp(prefix="org3_local_test_")
    try:
        ws_id = f"ws_local_{uuid4().hex[:6]}"
        adapter = LocalStorageAdapter(
            workspace_id=ws_id,
            storage_config={"base_path": temp_dir},
        )

        # 1. Inizializzazione 10 domini
        mapping = asyncio.run(adapter.ensure_domains_exist())
        assert len(mapping.domain_references) == 12
        for d_key in CANONICAL_DOMAINS:
            assert os.path.isdir(os.path.join(temp_dir, d_key))

        # 2. Scrittura file in 06_PRODUCT_RESEARCH
        content = b"# PRD Structura OS\nAutore: Nunzio Lella\n"
        item = asyncio.run(
            adapter.write_content(
                domain="06_PRODUCT_RESEARCH",
                filename="PRD_Structura.md",
                content=content,
            )
        )
        assert item.name == "PRD_Structura.md"
        assert item.domain == "06_PRODUCT_RESEARCH"
        assert item.size_bytes == len(content)
        assert item.sha256_hash is not None

        # 3. Listing con caching
        items = asyncio.run(adapter.list_items(domain="06_PRODUCT_RESEARCH"))
        assert len(items) == 1
        assert items[0].name == "PRD_Structura.md"

        # Verifica cache hit su seconda chiamata
        items_cached = asyncio.run(adapter.list_items(domain="06_PRODUCT_RESEARCH"))
        assert len(items_cached) == 1
        assert adapter.cache.get_stats()["hits"] >= 1

        # 4. Lettura file
        read_bytes = asyncio.run(adapter.read_content(item.item_id))
        assert read_bytes == content

        # 5. Fingerprint
        fp1 = asyncio.run(adapter.get_domain_fingerprint("06_PRODUCT_RESEARCH"))
        assert len(fp1) == 16

        # 6. Cancellazione
        deleted = asyncio.run(adapter.delete_item(item.item_id))
        assert deleted is True

        # Verifica svuotamento
        items_post_del = asyncio.run(adapter.list_items(domain="06_PRODUCT_RESEARCH"))
        assert len(items_post_del) == 0

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_google_drive_storage_adapter_simulated():
    """Verifica il GoogleDriveStorageAdapter in modalità simulata protetta."""
    ws_id = f"ws_gdrive_{uuid4().hex[:6]}"
    adapter = GoogleDriveStorageAdapter(
        workspace_id=ws_id,
        storage_config={"root_folder_id": "root_sim_123", "simulate": True},
    )

    # 1. Ensure domains
    mapping = asyncio.run(adapter.ensure_domains_exist())
    assert mapping.root_reference == "root_sim_123"
    assert len(mapping.domain_references) == 12

    # 2. Upload file in 01_CORPORATE
    doc_content = b"Visura Camerale Qubitdata Srl\nCapitale Sociale: 10.000 EUR\n"
    item = asyncio.run(
        adapter.write_content(
            domain="01_CORPORATE",
            filename="Visura_Camerale_2026.txt",
            content=doc_content,
        )
    )
    assert item.name == "Visura_Camerale_2026.txt"
    assert item.domain == "01_CORPORATE"

    # 3. List
    items = asyncio.run(adapter.list_items(domain="01_CORPORATE"))
    assert len(items) == 1
    assert items[0].name == "Visura_Camerale_2026.txt"

    # 4. Read
    content_downloaded = asyncio.run(adapter.read_content(item.item_id))
    assert content_downloaded == doc_content

    # 5. Fingerprint
    fp = asyncio.run(adapter.get_domain_fingerprint("01_CORPORATE"))
    assert len(fp) == 16

    # 6. Delete
    deleted = asyncio.run(adapter.delete_item(item.item_id))
    assert deleted is True


def test_s3_storage_adapter_simulated():
    """Verifica l'S3StorageAdapter in modalità simulata con partizione a prefissi."""
    ws_id = f"ws_s3_{uuid4().hex[:6]}"
    adapter = S3StorageAdapter(
        workspace_id=ws_id,
        storage_config={"bucket_name": "org3-vault", "simulate": True},
    )

    # 1. Mapping
    mapping = asyncio.run(adapter.ensure_domains_exist())
    assert "02_FINANCE_LEGAL" in mapping.domain_references
    assert mapping.domain_references["02_FINANCE_LEGAL"] == f"{ws_id}/02_FINANCE_LEGAL/"

    # 2. Write
    content = b"Bilancio Consuntivo 2025\nEBITDA: +35%\n"
    item = asyncio.run(
        adapter.write_content(
            domain="02_FINANCE_LEGAL",
            filename="Bilancio_2025.txt",
            content=content,
        )
    )
    assert item.name == "Bilancio_2025.txt"
    assert item.item_id == f"{ws_id}/02_FINANCE_LEGAL/Bilancio_2025.txt"

    # 3. List
    items = asyncio.run(adapter.list_items(domain="02_FINANCE_LEGAL"))
    assert len(items) == 1
    assert items[0].name == "Bilancio_2025.txt"

    # 4. Read & Delete
    read_data = asyncio.run(adapter.read_content(item.item_id))
    assert read_data == content
    assert asyncio.run(adapter.delete_item(item.item_id)) is True


def test_storage_adapter_factory():
    """Verifica la creazione e caching degli adapter dalla factory."""
    StorageAdapterFactory.reset_registry()

    ws_id_gdrive = "ws_fact_1"
    ad1 = StorageAdapterFactory.get_adapter(
        workspace_id=ws_id_gdrive,
        storage_provider=StorageProvider.GOOGLE_DRIVE,
        storage_config={"simulate": True},
    )
    assert isinstance(ad1, GoogleDriveStorageAdapter)

    # Verifica singleton per workspace
    ad1_cached = StorageAdapterFactory.get_adapter(
        workspace_id=ws_id_gdrive,
        storage_provider=StorageProvider.GOOGLE_DRIVE,
        storage_config={"simulate": True},
    )
    assert ad1 is ad1_cached

    # S3
    ad2 = StorageAdapterFactory.get_adapter(
        workspace_id="ws_fact_2",
        storage_provider=StorageProvider.S3,
        storage_config={"simulate": True},
    )
    assert isinstance(ad2, S3StorageAdapter)

    # Local
    ad3 = StorageAdapterFactory.get_adapter(
        workspace_id="ws_fact_3",
        storage_provider=StorageProvider.LOCAL_FS,
        storage_config={"base_path": "./test_fs"},
    )
    assert isinstance(ad3, LocalStorageAdapter)


def test_fastapi_storage_endpoints_full_lifecycle():
    """Verifica E2E tramite FastAPI TestClient del ciclo di vita storage con Neon Postgres."""
    # 1. Domini canonici pubblici
    resp_canon = client.get("/v1/storage/canonical-domains")
    assert resp_canon.status_code == 200
    data_canon = resp_canon.json()
    assert data_canon["total_domains"] == 12

    # 2. Cache stats pubbliche
    resp_cache = client.get("/v1/storage/cache/stats")
    assert resp_cache.status_code == 200

    # 3. Creazione Tenant & Workspace con Storage Locale
    slug = f"storage-tenant-{uuid4().hex[:6]}"
    resp_org = client.post(
        "/v1/organizations",
        json={
            "slug": slug,
            "name": "Storage Test Organization",
            "owner_email": "founder@storage-test.ai",
            "plan": "business",
        },
    )
    assert resp_org.status_code == 201
    org_id = resp_org.json()["id"]

    temp_storage_path = tempfile.mkdtemp(prefix="org3_api_storage_")
    try:
        resp_ws = client.post(
            f"/v1/organizations/{org_id}/workspaces",
            json={
                "name": "Primary Local Vault",
                "storage_provider": "local_fs",
                "storage_config": {"base_path": temp_storage_path},
                "is_primary": True,
            },
        )
        assert resp_ws.status_code == 201
        ws_id = resp_ws.json()["id"]

        # 4. Inizializzazione domini
        resp_init = client.post(f"/v1/workspaces/{ws_id}/storage/init-domains")
        assert resp_init.status_code == 200
        assert len(resp_init.json()["domain_references"]) == 12

        # 5. Status
        resp_stat = client.get(f"/v1/workspaces/{ws_id}/storage/status")
        assert resp_stat.status_code == 200
        assert resp_stat.json()["storage_provider"] == "local_fs"

        # 6. Upload documento in 04_STRATEGY_GOVERNANCE
        raw_text = "Master Roadmap 2026-2027\nQ1: Org3 Platform Launch\n"
        b64_content = base64.b64encode(raw_text.encode("utf-8")).decode("ascii")

        resp_upload = client.post(
            f"/v1/workspaces/{ws_id}/storage/domains/04_STRATEGY_GOVERNANCE/upload",
            json={
                "filename": "Roadmap_2026.md",
                "content_base64": b64_content,
                "mime_type": "text/markdown",
            },
        )
        assert resp_upload.status_code == 201
        uploaded_item = resp_upload.json()
        assert uploaded_item["name"] == "Roadmap_2026.md"
        item_id = uploaded_item["item_id"]

        # 7. Listing
        resp_list = client.get(f"/v1/workspaces/{ws_id}/storage/domains/04_STRATEGY_GOVERNANCE/items")
        assert resp_list.status_code == 200
        items = resp_list.json()
        assert len(items) == 1
        assert items[0]["name"] == "Roadmap_2026.md"

        # 8. Download Content
        # Encoding item_id per URL safe o query
        resp_content = client.get(f"/v1/workspaces/{ws_id}/storage/items/{item_id}/content")
        assert resp_content.status_code == 200
        assert resp_content.json()["text_content"] == raw_text

        # 9. Fingerprint
        resp_fp = client.get(f"/v1/workspaces/{ws_id}/storage/domains/04_STRATEGY_GOVERNANCE/fingerprint")
        assert resp_fp.status_code == 200
        assert len(resp_fp.json()["fingerprint"]) == 16

        # 10. Invalidate Cache
        resp_inval = client.post(f"/v1/workspaces/{ws_id}/storage/cache/invalidate")
        assert resp_inval.status_code == 200

        # 11. Delete Item
        resp_del = client.delete(f"/v1/workspaces/{ws_id}/storage/items/{item_id}")
        assert resp_del.status_code == 200
        assert resp_del.json()["deleted"] is True

    finally:
        shutil.rmtree(temp_storage_path, ignore_errors=True)
