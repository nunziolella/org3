"""Org3 Storage Adapter Factory & Registry.

Iscrive e istanzia connettori di storage multi-cloud per workspace,
riutilizzando le istanze e lo shield anti-quota in memoria.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from org3.models.multitenant import StorageProvider, Workspace
from org3.storage.base import BaseStorageAdapter
from org3.storage.cache import StorageCacheEngine
from org3.storage.gdrive import GoogleDriveStorageAdapter
from org3.storage.local import LocalStorageAdapter
from org3.storage.s3 import S3StorageAdapter


class StorageAdapterFactory:
    """Factory con cache delle istanze adapter per workspace."""

    _instances: Dict[str, BaseStorageAdapter] = {}
    _shared_cache: StorageCacheEngine = StorageCacheEngine()

    @classmethod
    def get_shared_cache(cls) -> StorageCacheEngine:
        return cls._shared_cache

    @classmethod
    def get_adapter(
        cls,
        workspace_id: str,
        storage_provider: StorageProvider,
        storage_config: Dict[str, Any],
        force_new: bool = False,
    ) -> BaseStorageAdapter:
        """Restituisce l'adapter associato al workspace, creandolo se necessario."""
        if not force_new and workspace_id in cls._instances:
            return cls._instances[workspace_id]

        adapter: BaseStorageAdapter
        if storage_provider == StorageProvider.GOOGLE_DRIVE:
            adapter = GoogleDriveStorageAdapter(
                workspace_id=workspace_id,
                storage_config=storage_config,
                cache=cls._shared_cache,
            )
        elif storage_provider in (StorageProvider.S3, StorageProvider.R2):
            adapter = S3StorageAdapter(
                workspace_id=workspace_id,
                storage_config=storage_config,
                cache=cls._shared_cache,
            )
        elif storage_provider == StorageProvider.LOCAL_FS:
            adapter = LocalStorageAdapter(
                workspace_id=workspace_id,
                storage_config=storage_config,
                cache=cls._shared_cache,
            )
        else:
            raise ValueError(f"Provider storage non supportato: {storage_provider}")

        cls._instances[workspace_id] = adapter
        return adapter

    @classmethod
    def get_adapter_for_workspace(cls, workspace: Workspace) -> BaseStorageAdapter:
        """Metodo di comodo che accetta direttamente il modello Workspace."""
        return cls.get_adapter(
            workspace_id=str(workspace.id),
            storage_provider=workspace.storage_provider,
            storage_config=workspace.storage_config,
        )

    @classmethod
    def reset_registry(cls) -> None:
        """Pulisce il registro delle istanze (utile nei test)."""
        cls._instances.clear()
        cls._shared_cache = StorageCacheEngine()
