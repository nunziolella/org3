"""Org3 S3 & Cloudflare R2 Cloud Storage Adapter.

Connette bucket S3-compatibili (AWS S3, Cloudflare R2, MinIO)
e struttura le chiavi secondo la partizione dei 10 domini persistenti:
`{workspace_id}/{domain_name}/{filename}`.

Include shield anti-quota e caching per ridurre i costi di richiesta S3 (GET/LIST).
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
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

logger = logging.getLogger("org3.storage.s3")


class S3StorageAdapter(BaseStorageAdapter):
    """Adapter per bucket S3 compatibili con partizione per dominio."""

    def __init__(
        self,
        workspace_id: str,
        storage_config: Dict[str, Any],
        cache: Optional[StorageCacheEngine] = None,
        simulate: bool = False,
    ):
        provider = StorageProvider.R2 if storage_config.get("provider") == "r2" else StorageProvider.S3
        super().__init__(workspace_id, provider, storage_config)
        self.bucket_name = storage_config.get("bucket_name", f"org3-workspace-{workspace_id}")
        self.endpoint_url = storage_config.get("endpoint_url")
        self.access_key_id = storage_config.get("access_key_id")
        self.secret_access_key = storage_config.get("secret_access_key")
        self.region_name = storage_config.get("region_name", "auto")
        self.cache = cache or StorageCacheEngine()

        # Modalità simulata
        self.is_simulated = simulate or storage_config.get("simulate", False) or (not self.access_key_id and not self.secret_access_key)
        self._sim_objects: Dict[str, Dict[str, Any]] = {}

    def _get_key_prefix(self, domain: Optional[str] = None) -> str:
        """Costruisce il prefisso S3 univoco per il tenant e il dominio."""
        if not domain:
            return f"{self.workspace_id}/"
        norm_domain = normalize_domain_key(domain)
        return f"{self.workspace_id}/{norm_domain}/"

    async def ensure_domains_exist(self) -> DomainFolderMap:
        """Inizializza i prefissi per i 10 domini persistenti nel bucket."""
        domain_refs: Dict[str, str] = {}
        for d_key in CANONICAL_DOMAINS:
            prefix = self._get_key_prefix(d_key)
            domain_refs[d_key] = prefix

        return DomainFolderMap(
            workspace_id=self.workspace_id,
            provider=self.provider,
            root_reference=f"s3://{self.bucket_name}/{self.workspace_id}",
            domain_references=domain_refs,
            last_synced_at=datetime.now(timezone.utc),
        )

    async def list_items(
        self,
        domain: Optional[str] = None,
        subpath: str = "",
        recursive: bool = False,
        force_refresh: bool = False,
    ) -> List[StorageItem]:
        """Elenca oggetti S3 con caching anti-quota e filtro per prefisso dominio."""
        norm_domain = normalize_domain_key(domain) if domain else None
        cache_id = f"{norm_domain or 'ROOT'}::{subpath}::{recursive}"

        if not force_refresh:
            cached = self.cache.get(self.workspace_id, "s3_list", cache_id)
            if cached is not None:
                return cached

        prefix = self._get_key_prefix(norm_domain)
        if subpath:
            prefix += f"{subpath.strip('/')}/"

        items: List[StorageItem] = []

        if self.is_simulated:
            for key, obj in self._sim_objects.items():
                if key.startswith(prefix):
                    rel_name = key[len(prefix):]
                    if not recursive and "/" in rel_name:
                        continue
                    items.append(
                        StorageItem(
                            item_id=key,
                            name=obj["filename"],
                            path=key[len(self.workspace_id) + 1:],
                            domain=norm_domain or "00_INDEX_RULES",
                            is_directory=False,
                            size_bytes=obj["size"],
                            mime_type=obj.get("mime_type", "application/octet-stream"),
                            modified_time=datetime.fromisoformat(obj["modified_time"]),
                            sha256_hash=obj.get("sha256"),
                            provider=self.provider,
                            metadata={"bucket": self.bucket_name, "s3_key": key},
                        )
                    )
            items.sort(key=lambda x: x.name.lower())
            self.cache.set(self.workspace_id, "s3_list", cache_id, items)
            return items

        # In caso di credenziali reali, boto3 o direct REST (se installato boto3)
        try:
            import boto3
            s3_client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name=self.region_name,
            )
            resp = s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            for content in resp.get("Contents", []):
                key = content["Key"]
                filename = key.split("/")[-1]
                if not filename:
                    continue
                items.append(
                    StorageItem(
                        item_id=key,
                        name=filename,
                        path=key[len(self.workspace_id) + 1:],
                        domain=norm_domain or "00_INDEX_RULES",
                        is_directory=False,
                        size_bytes=content["Size"],
                        mime_type="application/octet-stream",
                        modified_time=content["LastModified"].astimezone(timezone.utc),
                        sha256_hash=content.get("ETag", "").strip('"'),
                        provider=self.provider,
                        metadata={"bucket": self.bucket_name, "s3_key": key},
                    )
                )
        except Exception as e:
            logger.warning("S3 live listing failed (%s), fallback on virtual store", e)

        items.sort(key=lambda x: x.name.lower())
        self.cache.set(self.workspace_id, "s3_list", cache_id, items)
        return items

    async def get_item(self, item_id_or_path: str) -> Optional[StorageItem]:
        """Recupera metadati di un oggetto S3."""
        if self.is_simulated and item_id_or_path in self._sim_objects:
            obj = self._sim_objects[item_id_or_path]
            return StorageItem(
                item_id=item_id_or_path,
                name=obj["filename"],
                path=item_id_or_path[len(self.workspace_id) + 1:],
                domain=obj["domain"],
                is_directory=False,
                size_bytes=obj["size"],
                mime_type=obj.get("mime_type", "application/octet-stream"),
                modified_time=datetime.fromisoformat(obj["modified_time"]),
                sha256_hash=obj.get("sha256"),
                provider=self.provider,
                metadata={"bucket": self.bucket_name, "s3_key": item_id_or_path},
            )
        return None

    async def read_content(self, item_id_or_path: str) -> bytes:
        """Legge il contenuto binario dell'oggetto S3."""
        if self.is_simulated:
            if item_id_or_path in self._sim_objects:
                return self._sim_objects[item_id_or_path]["content"]
            raise FileNotFoundError(f"S3 Object {item_id_or_path} non trovato.")
        raise NotImplementedError("Live S3 download requires boto3 or REST credentials.")

    async def write_content(
        self,
        domain: str,
        filename: str,
        content: bytes,
        subpath: str = "",
        mime_type: str = "text/plain",
    ) -> StorageItem:
        """Carica un oggetto su S3/R2 e invalida la cache del dominio."""
        norm_domain = normalize_domain_key(domain)
        prefix = self._get_key_prefix(norm_domain)
        if subpath:
            prefix += f"{subpath.strip('/')}/"
        s3_key = f"{prefix}{filename}"
        sha256_val = hashlib.sha256(content).hexdigest()

        if self.is_simulated:
            self._sim_objects[s3_key] = {
                "key": s3_key,
                "filename": filename,
                "domain": norm_domain,
                "size": len(content),
                "mime_type": mime_type,
                "modified_time": datetime.now(timezone.utc).isoformat(),
                "content": content,
                "sha256": sha256_val,
            }
            self.cache.invalidate(self.workspace_id, "s3_list")

            return StorageItem(
                item_id=s3_key,
                name=filename,
                path=s3_key[len(self.workspace_id) + 1:],
                domain=norm_domain,
                is_directory=False,
                size_bytes=len(content),
                mime_type=mime_type,
                modified_time=datetime.now(timezone.utc),
                sha256_hash=sha256_val,
                provider=self.provider,
                metadata={"bucket": self.bucket_name, "s3_key": s3_key},
            )

        raise NotImplementedError("Live S3 upload requires boto3 or signed S3 REST v4.")

    async def delete_item(self, item_id_or_path: str) -> bool:
        """Rimuove un oggetto da S3 e invalida la cache."""
        if self.is_simulated:
            if item_id_or_path in self._sim_objects:
                del self._sim_objects[item_id_or_path]
                self.cache.invalidate(self.workspace_id, "s3_list")
                return True
            return False
        return False

    async def get_domain_fingerprint(self, domain: str) -> str:
        """Calcola un'impronta complessiva SHA256 dei file presenti nel dominio."""
        items = await self.list_items(domain=domain, recursive=False)
        raw = "|".join(f"{it.name}:{it.size_bytes}:{it.version_fingerprint}" for it in items)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
