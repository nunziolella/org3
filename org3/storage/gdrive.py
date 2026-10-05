"""Org3 Google Drive Cloud Storage Adapter con Caching Anti-Quota.

Connette la Root Folder Google Drive dell'azienda e mappa le sottocartelle
sui 10 Domini Persistenti (`01_CORPORATE`..`10_OPERATIONS_RECORDS`).

Caratteristiche di Ingegneria:
1. Supporto Service Account (GCP) o OAuth2 Bearer Token.
2. Modalità Simulazione / Mock integrata per collaudo CI/CD e tenant non ancora attivati.
3. Anti-Quota Shield: proiezione campi leggeri (`fields=nextPageToken, files(...)`),
   caching a TTL 300s (5 min), monitoraggio rolling window 100s ed exponential backoff con jitter su HTTP 429.
4. Auto-Invalidation su creazione/cancellazione file.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx

from org3.models.multitenant import StorageProvider
from org3.storage.base import (
    CANONICAL_DOMAINS,
    BaseStorageAdapter,
    DomainFolderMap,
    StorageItem,
    normalize_domain_key,
)
from org3.storage.cache import StorageCacheEngine

logger = logging.getLogger("org3.storage.gdrive")

GDRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
GDRIVE_UPLOAD_BASE = "https://www.googleapis.com/upload/drive/v3"
FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"


class GoogleDriveStorageAdapter(BaseStorageAdapter):
    """Adapter storage per Google Drive v3 con shield anti-quota."""

    def __init__(
        self,
        workspace_id: str,
        storage_config: Dict[str, Any],
        cache: Optional[StorageCacheEngine] = None,
        simulate: bool = False,
    ):
        super().__init__(workspace_id, StorageProvider.GOOGLE_DRIVE, storage_config)
        self.root_folder_id = storage_config.get("root_folder_id", "root")
        self.credentials_json = storage_config.get("credentials_json")
        self.access_token = storage_config.get("access_token")
        self.cache = cache or StorageCacheEngine()

        # Se simulate è True o mancano credenziali reali, attiva simulatore virtuale
        self.is_simulated = simulate or storage_config.get("simulate", False) or (not self.credentials_json and not self.access_token)
        
        # Struttura dati per simulazione virtuale
        self._sim_files: Dict[str, Dict[str, Any]] = {}
        self._sim_folders: Dict[str, Dict[str, Any]] = {}
        self._sim_folder_map: Dict[str, str] = {} # domain_name -> folder_id

        if self.is_simulated:
            self._init_simulation()

    def _init_simulation(self) -> None:
        """Inizializza l'albero simulato in memoria per test o tenant in onboarding."""
        self._sim_folders[self.root_folder_id] = {
            "id": self.root_folder_id,
            "name": "Org3_Company_Root",
            "parents": [],
            "mimeType": FOLDER_MIME_TYPE,
            "modifiedTime": datetime.now(timezone.utc).isoformat(),
        }
        for d_key in CANONICAL_DOMAINS:
            f_id = f"sim_folder_{d_key.lower()}"
            self._sim_folders[f_id] = {
                "id": f_id,
                "name": d_key,
                "parents": [self.root_folder_id],
                "mimeType": FOLDER_MIME_TYPE,
                "modifiedTime": datetime.now(timezone.utc).isoformat(),
            }
            self._sim_folder_map[d_key] = f_id

    async def _get_auth_headers(self) -> Dict[str, str]:
        """Genera header di autenticazione Bearer per Google Drive API."""
        if self.is_simulated:
            return {"Authorization": "Bearer sim_mock_token"}

        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}

        if self.credentials_json:
            try:
                from google.oauth2 import service_account
                import google.auth.transport.requests

                creds_dict = self.credentials_json
                if isinstance(creds_dict, str):
                    creds_dict = json.loads(creds_dict)

                scopes = ["https://www.googleapis.com/auth/drive"]
                creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scopes)
                req = google.auth.transport.requests.Request()
                creds.refresh(req)
                return {"Authorization": f"Bearer {creds.token}"}
            except Exception as e:
                logger.error("Failed to load Google Service Account credentials: %s", e)
                raise RuntimeError(f"Google Drive credentials error: {e}")

        raise ValueError("Nessun token OAuth o Service Account configurato per Google Drive.")

    async def ensure_domains_exist(self) -> DomainFolderMap:
        """Mappa o crea le 10 cartelle canoniche sotto la root Google Drive."""
        if self.is_simulated:
            return DomainFolderMap(
                workspace_id=self.workspace_id,
                provider=self.provider,
                root_reference=self.root_folder_id,
                domain_references=dict(self._sim_folder_map),
                last_synced_at=datetime.now(timezone.utc),
            )

        headers = await self._get_auth_headers()
        domain_refs: Dict[str, str] = {}

        async def _query_existing_folders():
            async with httpx.AsyncClient(timeout=10.0) as client:
                query = f"'{self.root_folder_id}' in parents and mimeType = '{FOLDER_MIME_TYPE}' and trashed = false"
                url = f"{GDRIVE_API_BASE}/files?q={query}&fields=files(id,name)"
                resp = await client.get(url, headers=headers)
                if resp.status_code == 429:
                    raise RuntimeError("HTTP 429 Too Many Requests")
                resp.raise_for_status()
                return resp.json().get("files", [])

        existing_folders = await self.cache.execute_with_anti_quota_retry(
            self.workspace_id,
            "ensure_domains_exist.list",
            _query_existing_folders,
        )

        existing_map = {f["name"]: f["id"] for f in existing_folders}

        for domain_name in CANONICAL_DOMAINS:
            if domain_name in existing_map:
                domain_refs[domain_name] = existing_map[domain_name]
            else:
                # Crea la cartella mancante
                async def _create_folder(d_name=domain_name):
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        payload = {
                            "name": d_name,
                            "mimeType": FOLDER_MIME_TYPE,
                            "parents": [self.root_folder_id],
                        }
                        resp = await client.post(f"{GDRIVE_API_BASE}/files", json=payload, headers=headers)
                        if resp.status_code == 429:
                            raise RuntimeError("HTTP 429 Too Many Requests")
                        resp.raise_for_status()
                        return resp.json()["id"]

                folder_id = await self.cache.execute_with_anti_quota_retry(
                    self.workspace_id,
                    f"create_folder.{domain_name}",
                    _create_folder,
                )
                domain_refs[domain_name] = folder_id

        return DomainFolderMap(
            workspace_id=self.workspace_id,
            provider=self.provider,
            root_reference=self.root_folder_id,
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
        """Elenca file con caching anti-quota e proiezione di metadati compatti."""
        norm_domain = normalize_domain_key(domain) if domain else None
        cache_id = f"{norm_domain or 'ROOT'}::{subpath}::{recursive}"

        if not force_refresh:
            cached = self.cache.get(self.workspace_id, "gdrive_list", cache_id)
            if cached is not None:
                return cached

        # Se simulato, elenca dai record virtuali
        if self.is_simulated:
            items: List[StorageItem] = []
            target_folder_id = self._sim_folder_map.get(norm_domain) if norm_domain else self.root_folder_id

            for f_id, f_data in self._sim_files.items():
                if target_folder_id in f_data["parents"]:
                    items.append(
                        StorageItem(
                            item_id=f_id,
                            name=f_data["name"],
                            path=f"{norm_domain or 'ROOT'}/{f_data['name']}",
                            domain=norm_domain or "00_INDEX_RULES",
                            is_directory=False,
                            size_bytes=f_data.get("size", 0),
                            mime_type=f_data.get("mimeType", "application/octet-stream"),
                            modified_time=datetime.fromisoformat(f_data["modifiedTime"]),
                            sha256_hash=f_data.get("sha256"),
                            provider=self.provider,
                            metadata={"gdrive_file_id": f_id},
                        )
                    )

            # Salva in cache
            self.cache.set(self.workspace_id, "gdrive_list", cache_id, items)
            return items

        # Chiamata live a Google Drive v3 con proiezione campi leggeri
        headers = await self._get_auth_headers()
        domain_mapping = await self.ensure_domains_exist()
        parent_id = domain_mapping.domain_references.get(norm_domain, self.root_folder_id)

        async def _fetch_gdrive_files():
            async with httpx.AsyncClient(timeout=10.0) as client:
                query = f"'{parent_id}' in parents and trashed = false"
                fields = "files(id, name, mimeType, size, modifiedTime, md5Checksum)"
                url = f"{GDRIVE_API_BASE}/files?q={query}&fields={fields}&pageSize=1000"
                resp = await client.get(url, headers=headers)
                if resp.status_code == 429:
                    raise RuntimeError("HTTP 429 Too Many Requests")
                resp.raise_for_status()
                return resp.json().get("files", [])

        g_files = await self.cache.execute_with_anti_quota_retry(
            self.workspace_id,
            f"list_files.{norm_domain}",
            _fetch_gdrive_files,
        )

        items: List[StorageItem] = []
        for gf in g_files:
            is_dir = gf.get("mimeType") == FOLDER_MIME_TYPE
            size = int(gf.get("size", 0)) if not is_dir else 0
            mod_time = datetime.fromisoformat(gf.get("modifiedTime").replace("Z", "+00:00"))

            items.append(
                StorageItem(
                    item_id=gf["id"],
                    name=gf["name"],
                    path=f"{norm_domain}/{gf['name']}",
                    domain=norm_domain or "00_INDEX_RULES",
                    is_directory=is_dir,
                    size_bytes=size,
                    mime_type=gf.get("mimeType", "application/octet-stream"),
                    modified_time=mod_time,
                    sha256_hash=gf.get("md5Checksum"), # Google Drive fornisce MD5 checksum nativo
                    provider=self.provider,
                    metadata={"gdrive_file_id": gf["id"]},
                )
            )

        items.sort(key=lambda x: (not x.is_directory, x.name.lower()))
        self.cache.set(self.workspace_id, "gdrive_list", cache_id, items)
        return items

    async def get_item(self, item_id_or_path: str) -> Optional[StorageItem]:
        """Recupera i metadati di un file Google Drive."""
        if self.is_simulated:
            if item_id_or_path in self._sim_files:
                f_data = self._sim_files[item_id_or_path]
                return StorageItem(
                    item_id=item_id_or_path,
                    name=f_data["name"],
                    path=f_data["name"],
                    domain="01_CORPORATE",
                    is_directory=False,
                    size_bytes=f_data.get("size", 0),
                    mime_type=f_data.get("mimeType", "text/plain"),
                    modified_time=datetime.fromisoformat(f_data["modifiedTime"]),
                    sha256_hash=f_data.get("sha256"),
                    provider=self.provider,
                )
            return None

        headers = await self._get_auth_headers()

        async def _fetch():
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{GDRIVE_API_BASE}/files/{item_id_or_path}?fields=id,name,mimeType,size,modifiedTime,md5Checksum"
                resp = await client.get(url, headers=headers)
                if resp.status_code == 404:
                    return None
                if resp.status_code == 429:
                    raise RuntimeError("HTTP 429 Too Many Requests")
                resp.raise_for_status()
                return resp.json()

        gf = await self.cache.execute_with_anti_quota_retry(
            self.workspace_id,
            f"get_item.{item_id_or_path}",
            _fetch,
        )
        if not gf:
            return None

        is_dir = gf.get("mimeType") == FOLDER_MIME_TYPE
        return StorageItem(
            item_id=gf["id"],
            name=gf["name"],
            path=gf["name"],
            domain="00_INDEX_RULES",
            is_directory=is_dir,
            size_bytes=int(gf.get("size", 0)) if not is_dir else 0,
            mime_type=gf.get("mimeType", "application/octet-stream"),
            modified_time=datetime.fromisoformat(gf.get("modifiedTime").replace("Z", "+00:00")),
            sha256_hash=gf.get("md5Checksum"),
            provider=self.provider,
            metadata={"gdrive_file_id": gf["id"]},
        )

    async def read_content(self, item_id_or_path: str) -> bytes:
        """Scarica il contenuto binario del file da Google Drive."""
        if self.is_simulated:
            if item_id_or_path in self._sim_files:
                return self._sim_files[item_id_or_path]["content"]
            raise FileNotFoundError(f"File simulato {item_id_or_path} non trovato.")

        headers = await self._get_auth_headers()

        async def _download():
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{GDRIVE_API_BASE}/files/{item_id_or_path}?alt=media"
                resp = await client.get(url, headers=headers)
                if resp.status_code == 429:
                    raise RuntimeError("HTTP 429 Too Many Requests")
                resp.raise_for_status()
                return resp.content

        return await self.cache.execute_with_anti_quota_retry(
            self.workspace_id,
            f"read_content.{item_id_or_path}",
            _download,
        )

    async def write_content(
        self,
        domain: str,
        filename: str,
        content: bytes,
        subpath: str = "",
        mime_type: str = "text/plain",
    ) -> StorageItem:
        """Carica un file su Google Drive e invalida la cache del dominio."""
        norm_domain = normalize_domain_key(domain)

        if self.is_simulated:
            f_id = f"sim_file_{hashlib.md5((filename + str(datetime.now())).encode()).hexdigest()[:8]}"
            folder_id = self._sim_folder_map.get(norm_domain, self.root_folder_id)
            sha256_val = hashlib.sha256(content).hexdigest()

            self._sim_files[f_id] = {
                "id": f_id,
                "name": filename,
                "parents": [folder_id],
                "size": len(content),
                "mimeType": mime_type,
                "modifiedTime": datetime.now(timezone.utc).isoformat(),
                "content": content,
                "sha256": sha256_val,
            }

            # Invalida cache
            self.cache.invalidate(self.workspace_id, "gdrive_list")

            return StorageItem(
                item_id=f_id,
                name=filename,
                path=f"{norm_domain}/{filename}",
                domain=norm_domain,
                is_directory=False,
                size_bytes=len(content),
                mime_type=mime_type,
                modified_time=datetime.now(timezone.utc),
                sha256_hash=sha256_val,
                provider=self.provider,
                metadata={"gdrive_file_id": f_id},
            )

        headers = await self._get_auth_headers()
        domain_mapping = await self.ensure_domains_exist()
        parent_id = domain_mapping.domain_references.get(norm_domain, self.root_folder_id)

        metadata = {
            "name": filename,
            "parents": [parent_id],
        }

        # Multipart upload per Google Drive v3
        files = {
            "data": ("metadata", json.dumps(metadata), "application/json; charset=UTF-8"),
            "file": (filename, content, mime_type),
        }

        async def _upload():
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{GDRIVE_UPLOAD_BASE}/files?uploadType=multipart&fields=id,name,size,modifiedTime,md5Checksum"
                # Rimuovi Content-Type da headers per lasciare che httpx gestisca il multipart boundary
                upload_headers = {k: v for k, v in headers.items() if k.lower() != "content-type"}
                resp = await client.post(url, files=files, headers=upload_headers)
                if resp.status_code == 429:
                    raise RuntimeError("HTTP 429 Too Many Requests")
                resp.raise_for_status()
                return resp.json()

        uploaded = await self.cache.execute_with_anti_quota_retry(
            self.workspace_id,
            f"write_content.{norm_domain}.{filename}",
            _upload,
        )

        # Invalida selettivamente la cache delle liste per questo dominio
        self.cache.invalidate(self.workspace_id, "gdrive_list")

        return StorageItem(
            item_id=uploaded["id"],
            name=filename,
            path=f"{norm_domain}/{filename}",
            domain=norm_domain,
            is_directory=False,
            size_bytes=len(content),
            mime_type=mime_type,
            modified_time=datetime.fromisoformat(uploaded.get("modifiedTime").replace("Z", "+00:00")),
            sha256_hash=uploaded.get("md5Checksum"),
            provider=self.provider,
            metadata={"gdrive_file_id": uploaded["id"]},
        )

    async def delete_item(self, item_id_or_path: str) -> bool:
        """Elimina un file o lo sposta nel cestino di Google Drive."""
        if self.is_simulated:
            if item_id_or_path in self._sim_files:
                del self._sim_files[item_id_or_path]
                self.cache.invalidate(self.workspace_id, "gdrive_list")
                return True
            return False

        headers = await self._get_auth_headers()

        async def _delete():
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{GDRIVE_API_BASE}/files/{item_id_or_path}"
                resp = await client.delete(url, headers=headers)
                if resp.status_code == 429:
                    raise RuntimeError("HTTP 429 Too Many Requests")
                if resp.status_code == 404:
                    return False
                resp.raise_for_status()
                return True

        result = await self.cache.execute_with_anti_quota_retry(
            self.workspace_id,
            f"delete_item.{item_id_or_path}",
            _delete,
        )

        self.cache.invalidate(self.workspace_id, "gdrive_list")
        return result

    async def get_domain_fingerprint(self, domain: str) -> str:
        """Calcola un'impronta complessiva SHA256 dei file presenti nel dominio."""
        items = await self.list_items(domain=domain, recursive=False)
        raw = "|".join(f"{it.name}:{it.size_bytes}:{it.version_fingerprint}" for it in items)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
