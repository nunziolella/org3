"""Org3 Local Filesystem Storage Adapter.

Consente l'accesso diretto al filesystem locale (utile per sviluppo, test,
e deployment self-hosted/edge senza dipendenze cloud esterne).
Implementa tutte le funzionalità di mapping sui 10 domini persistenti,
calcolo fingerprint SHA256 e integrazione con lo shield anti-quota.
"""

from __future__ import annotations

import hashlib
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from org3.models.multitenant import StorageProvider
from org3.storage.base import (
    CANONICAL_DOMAINS,
    BaseStorageAdapter,
    DomainFolderMap,
    StorageItem,
    normalize_domain_key,
)
from org3.storage.cache import StorageCacheEngine


class LocalStorageAdapter(BaseStorageAdapter):
    """Adapter storage su filesystem locale."""

    def __init__(
        self,
        workspace_id: str,
        storage_config: Dict[str, Any],
        cache: Optional[StorageCacheEngine] = None,
    ):
        super().__init__(workspace_id, StorageProvider.LOCAL_FS, storage_config)
        self.root_path = Path(storage_config.get("base_path", os.path.join(".", "storage_data", workspace_id)))
        self.root_path.mkdir(parents=True, exist_ok=True)
        self.cache = cache or StorageCacheEngine()

    async def ensure_domains_exist(self) -> DomainFolderMap:
        """Crea le cartelle per tutti i 10 domini canonici (più 00 e 99) nella root locale."""
        domain_refs: Dict[str, str] = {}
        for domain_name in CANONICAL_DOMAINS:
            domain_dir = self.root_path / domain_name
            domain_dir.mkdir(parents=True, exist_ok=True)
            domain_refs[domain_name] = str(domain_dir.resolve())

        mapping = DomainFolderMap(
            workspace_id=self.workspace_id,
            provider=self.provider,
            root_reference=str(self.root_path.resolve()),
            domain_references=domain_refs,
            last_synced_at=datetime.now(timezone.utc),
        )
        return mapping

    async def list_items(
        self,
        domain: Optional[str] = None,
        subpath: str = "",
        recursive: bool = False,
        force_refresh: bool = False,
    ) -> List[StorageItem]:
        """Elenca file e cartelle con caching a TTL 5 minuti."""
        norm_domain = normalize_domain_key(domain) if domain else None
        cache_id = f"{norm_domain or 'ROOT'}::{subpath}::{recursive}"

        if not force_refresh:
            cached = self.cache.get(self.workspace_id, "list", cache_id)
            if cached is not None:
                return cached

        target_dir = self.root_path
        if norm_domain:
            target_dir = target_dir / norm_domain
        if subpath:
            target_dir = target_dir / subpath

        if not target_dir.exists():
            return []

        items: List[StorageItem] = []
        pattern = "**/*" if recursive else "*"

        for entry in target_dir.glob(pattern):
            rel_path = entry.relative_to(self.root_path).as_posix()
            parts = rel_path.split("/")
            entry_domain = normalize_domain_key(parts[0]) if parts else "00_INDEX_RULES"

            stat = entry.stat()
            modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            is_dir = entry.is_dir()
            size = 0 if is_dir else stat.st_size

            sha256_val = None
            if not is_dir and size <= 10 * 1024 * 1024: # Calcola sha256 per file <= 10MB
                try:
                    with open(entry, "rb") as f:
                        sha256_val = hashlib.sha256(f.read()).hexdigest()
                except Exception:
                    pass

            item = StorageItem(
                item_id=str(entry.resolve()),
                name=entry.name,
                path=rel_path,
                domain=entry_domain,
                is_directory=is_dir,
                size_bytes=size,
                mime_type="inode/directory" if is_dir else "application/octet-stream",
                modified_time=modified,
                sha256_hash=sha256_val,
                provider=self.provider,
                metadata={"local_path": str(entry.resolve())},
            )
            items.append(item)

        # Ordina per directory prima, poi per nome
        items.sort(key=lambda x: (not x.is_directory, x.name.lower()))

        # Salva in cache
        self.cache.set(self.workspace_id, "list", cache_id, items)
        return items

    async def get_item(self, item_id_or_path: str) -> Optional[StorageItem]:
        """Recupera metadati di un elemento locale."""
        target = Path(item_id_or_path)
        if not target.is_absolute():
            target = self.root_path / item_id_or_path

        if not target.exists():
            return None

        stat = target.stat()
        is_dir = target.is_dir()
        rel_path = target.relative_to(self.root_path).as_posix() if target.is_relative_to(self.root_path) else target.name
        parts = rel_path.split("/")
        entry_domain = normalize_domain_key(parts[0]) if parts else "00_INDEX_RULES"

        sha256_val = None
        if not is_dir and stat.st_size <= 10 * 1024 * 1024:
            try:
                with open(target, "rb") as f:
                    sha256_val = hashlib.sha256(f.read()).hexdigest()
            except Exception:
                pass

        return StorageItem(
            item_id=str(target.resolve()),
            name=target.name,
            path=rel_path,
            domain=entry_domain,
            is_directory=is_dir,
            size_bytes=0 if is_dir else stat.st_size,
            mime_type="inode/directory" if is_dir else "application/octet-stream",
            modified_time=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            sha256_hash=sha256_val,
            provider=self.provider,
            metadata={"local_path": str(target.resolve())},
        )

    async def read_content(self, item_id_or_path: str) -> bytes:
        """Legge il contenuto binario del file."""
        target = Path(item_id_or_path)
        if not target.is_absolute():
            target = self.root_path / item_id_or_path

        if not target.exists() or target.is_dir():
            raise FileNotFoundError(f"File non trovato o è una directory: {item_id_or_path}")

        with open(target, "rb") as f:
            return f.read()

    async def write_content(
        self,
        domain: str,
        filename: str,
        content: bytes,
        subpath: str = "",
        mime_type: str = "text/plain",
    ) -> StorageItem:
        """Scrive un file nel dominio specificato e invalida la cache."""
        norm_domain = normalize_domain_key(domain)
        dest_dir = self.root_path / norm_domain
        if subpath:
            dest_dir = dest_dir / subpath
        dest_dir.mkdir(parents=True, exist_ok=True)

        target_file = dest_dir / filename
        with open(target_file, "wb") as f:
            f.write(content)

        # Invalida cache per questo dominio
        self.cache.invalidate(self.workspace_id, "list")

        sha256_val = hashlib.sha256(content).hexdigest()
        rel_path = target_file.relative_to(self.root_path).as_posix()

        return StorageItem(
            item_id=str(target_file.resolve()),
            name=filename,
            path=rel_path,
            domain=norm_domain,
            is_directory=False,
            size_bytes=len(content),
            mime_type=mime_type,
            modified_time=datetime.now(timezone.utc),
            sha256_hash=sha256_val,
            provider=self.provider,
            metadata={"local_path": str(target_file.resolve())},
        )

    async def delete_item(self, item_id_or_path: str) -> bool:
        """Elimina file o cartella dal filesystem locale e invalida la cache."""
        target = Path(item_id_or_path)
        if not target.is_absolute():
            target = self.root_path / item_id_or_path

        if not target.exists():
            return False

        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()

        self.cache.invalidate(self.workspace_id, "list")
        return True

    async def get_domain_fingerprint(self, domain: str) -> str:
        """Calcola un'impronta complessiva SHA256 dei file presenti nel dominio."""
        items = await self.list_items(domain=domain, recursive=True)
        raw = "|".join(f"{it.name}:{it.size_bytes}:{it.version_fingerprint}" for it in items)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
