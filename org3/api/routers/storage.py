"""Router for Org3 Multi-Cloud Storage and 10 Persistent Domains.

Espone le API REST per la gestione dello storage agnostico (Google Drive, S3, Local FS),
il mapping delle directory sui 10 domini persistenti e il monitoraggio dello shield anti-quota.
"""

from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from org3.api.db import get_db
from org3.models.multitenant import StorageProvider, Workspace
from org3.storage.base import (
    CANONICAL_DOMAINS,
    DomainFolderMap,
    StorageItem,
    normalize_domain_key,
)
from org3.storage.factory import StorageAdapterFactory

router = APIRouter(prefix="/v1", tags=["Storage & 10 Persistent Domains"])


class UploadItemRequest(BaseModel):
    filename: str = Field(..., max_length=255, description="Nome del file (es. 'PRD_Piattaforma_v1.md')")
    content_base64: str = Field(..., description="Payload codificato in base64")
    subpath: str = Field(default="", description="Sottocartella facoltativa dentro il dominio")
    mime_type: str = Field(default="text/plain", description="MIME type del contenuto")


class StorageStatusResponse(BaseModel):
    workspace_id: str
    workspace_name: str
    storage_provider: StorageProvider
    root_reference: str
    domain_references: Dict[str, str]
    cache_stats: Dict[str, Any]


def _get_workspace_or_404(workspace_id: str, db) -> Workspace:
    """Helper di risoluzione workspace da Neon Postgres."""
    cur = db.cursor()
    cur.execute(
        """
        SELECT id, org_id, name, storage_provider, storage_config, is_primary, created_at
        FROM org3_workspaces
        WHERE id = %s;
    """,
        (workspace_id,),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace con id '{workspace_id}' non trovato.",
        )
    return Workspace(**dict(row))


@router.get("/storage/canonical-domains")
def get_canonical_domains():
    """Restituisce l'elenco dei 10 domini persistenti canonici e le loro descrizioni."""
    return {
        "domains": list(CANONICAL_DOMAINS.values()),
        "total_domains": len(CANONICAL_DOMAINS),
    }


@router.get("/storage/cache/stats")
def get_cache_stats():
    """Restituisce le statistiche operative globali dello shield anti-quota."""
    return StorageAdapterFactory.get_shared_cache().get_stats()


@router.get("/workspaces/{workspace_id}/storage/status", response_model=StorageStatusResponse)
async def get_storage_status(workspace_id: str, db=Depends(get_db)):
    """Verifica lo stato della connessione storage e il mapping dei domini per il workspace."""
    workspace = _get_workspace_or_404(workspace_id, db)
    adapter = StorageAdapterFactory.get_adapter_for_workspace(workspace)
    mapping = await adapter.ensure_domains_exist()
    cache_stats = StorageAdapterFactory.get_shared_cache().get_stats()

    return StorageStatusResponse(
        workspace_id=str(workspace.id),
        workspace_name=workspace.name,
        storage_provider=workspace.storage_provider,
        root_reference=mapping.root_reference,
        domain_references=mapping.domain_references,
        cache_stats=cache_stats,
    )


@router.post("/workspaces/{workspace_id}/storage/init-domains", response_model=DomainFolderMap)
async def init_domains(workspace_id: str, db=Depends(get_db)):
    """Inizializza o convalida la presenza delle cartelle per tutti i 10 domini nello storage."""
    workspace = _get_workspace_or_404(workspace_id, db)
    adapter = StorageAdapterFactory.get_adapter_for_workspace(workspace)
    mapping = await adapter.ensure_domains_exist()
    return mapping


@router.get("/workspaces/{workspace_id}/storage/domains/{domain}/items", response_model=List[StorageItem])
async def list_domain_items(
    workspace_id: str,
    domain: str,
    subpath: str = Query(default=""),
    recursive: bool = Query(default=False),
    force_refresh: bool = Query(default=False),
    db=Depends(get_db),
):
    """Elenca file e directory memorizzati nel dominio con caching anti-quota TTL 5m."""
    workspace = _get_workspace_or_404(workspace_id, db)
    adapter = StorageAdapterFactory.get_adapter_for_workspace(workspace)
    norm_domain = normalize_domain_key(domain)

    items = await adapter.list_items(
        domain=norm_domain,
        subpath=subpath,
        recursive=recursive,
        force_refresh=force_refresh,
    )
    return items


@router.post("/workspaces/{workspace_id}/storage/domains/{domain}/upload", response_model=StorageItem, status_code=status.HTTP_201_CREATED)
async def upload_domain_item(
    workspace_id: str,
    domain: str,
    req: UploadItemRequest,
    db=Depends(get_db),
):
    """Carica un file nel dominio specificato invalidando la cache in modo atomico."""
    workspace = _get_workspace_or_404(workspace_id, db)
    adapter = StorageAdapterFactory.get_adapter_for_workspace(workspace)
    norm_domain = normalize_domain_key(domain)

    try:
        content_bytes = base64.b64decode(req.content_base64)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Decodifica base64 fallita: {e}",
        )

    item = await adapter.write_content(
        domain=norm_domain,
        filename=req.filename,
        content=content_bytes,
        subpath=req.subpath,
        mime_type=req.mime_type,
    )
    return item


@router.get("/workspaces/{workspace_id}/storage/domains/{domain}/fingerprint")
async def get_domain_fingerprint(
    workspace_id: str,
    domain: str,
    db=Depends(get_db),
):
    """Restituisce l'impronta complessiva SHA256 dei file nel dominio per drift detection."""
    workspace = _get_workspace_or_404(workspace_id, db)
    adapter = StorageAdapterFactory.get_adapter_for_workspace(workspace)
    norm_domain = normalize_domain_key(domain)
    fingerprint = await adapter.get_domain_fingerprint(norm_domain)

    return {
        "workspace_id": str(workspace.id),
        "domain": norm_domain,
        "fingerprint": fingerprint,
    }


@router.get("/workspaces/{workspace_id}/storage/items/{item_id:path}/content")
async def read_item_content(
    workspace_id: str,
    item_id: str,
    db=Depends(get_db),
):
    """Scarica il contenuto di un file restituendolo in base64 e utf-8."""
    workspace = _get_workspace_or_404(workspace_id, db)
    adapter = StorageAdapterFactory.get_adapter_for_workspace(workspace)

    try:
        content_bytes = await adapter.read_content(item_id)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File non trovato.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    b64_content = base64.b64encode(content_bytes).decode("ascii")
    text_content = None
    try:
        text_content = content_bytes.decode("utf-8")
    except Exception:
        pass

    return {
        "item_id": item_id,
        "size_bytes": len(content_bytes),
        "content_base64": b64_content,
        "text_content": text_content,
    }


@router.delete("/workspaces/{workspace_id}/storage/items/{item_id:path}")
async def delete_item(
    workspace_id: str,
    item_id: str,
    db=Depends(get_db),
):
    """Rimuove un file dallo storage del workspace."""
    workspace = _get_workspace_or_404(workspace_id, db)
    adapter = StorageAdapterFactory.get_adapter_for_workspace(workspace)
    deleted = await adapter.delete_item(item_id)

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File non trovato o già rimosso.")

    return {"deleted": True, "item_id": item_id}


@router.post("/workspaces/{workspace_id}/storage/cache/invalidate")
def invalidate_cache(
    workspace_id: str,
    domain: Optional[str] = Query(default=None),
    db=Depends(get_db),
):
    """Invalida manualmente la cache del workspace o di uno specifico dominio."""
    workspace = _get_workspace_or_404(workspace_id, db)
    cache = StorageAdapterFactory.get_shared_cache()
    norm_domain = normalize_domain_key(domain) if domain else None
    count = cache.invalidate(str(workspace.id), scope=norm_domain)
    return {"workspace_id": str(workspace.id), "invalidated_entries": count}
