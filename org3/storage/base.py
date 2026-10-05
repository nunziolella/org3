"""Org3 Sovereign Storage: Base Models and Abstract Storage Adapter.

Invarianti dal Persistent Information Layer (AIPROD 03_MEMORY_SYSTEM):
1. Lo storage fisico risponde a: 'Che tipo di informazione è?' (10 domini funzionali).
2. Org3 risponde a: 'Chi, in quale ruolo, funzione, divisione ha prodotto o accede a questa informazione?'
3. Nessuna duplicazione fisica: ruoli e divisioni sono viste virtuali proiettate su questo layer.
4. Anti-Quota & Caching: tutti gli accessi transitano da uno shield con TTL 5m e fingerprint SHA256/modifiedTime.
"""

from __future__ import annotations

import abc
import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from org3.core.ontology import FunctionalDomain
from org3.models.multitenant import StorageProvider


# Canonical 10 Persistent Domains + Index & Archive
CANONICAL_DOMAINS: Dict[str, Dict[str, str]] = {
    "00_INDEX_RULES": {
        "code": "00",
        "name": "00_INDEX_RULES",
        "title": "Index, Rules & Governance",
        "description": "Indici canonici, registri di sistema, vocabolari e regole ontologiche",
    },
    "01_CORPORATE": {
        "code": "01",
        "name": "01_CORPORATE",
        "title": "Corporate, Identity & Statuto",
        "description": "Documenti societari, visure, statuti, patti parasociali e compagine sociale",
    },
    "02_FINANCE_LEGAL": {
        "code": "02",
        "name": "02_FINANCE_LEGAL",
        "title": "Finance, Legal & Contracts",
        "description": "Bilanci, fatture, contratti fornitore, coordinate bancarie, compliance fiscale",
    },
    "03_HUMAN_ORGANIZATION": {
        "code": "03",
        "name": "03_HUMAN_ORGANIZATION",
        "title": "Human & Organization",
        "description": "Organigramma, ruoli, contratti di delega, team roster e profili agenti",
    },
    "04_STRATEGY_GOVERNANCE": {
        "code": "04",
        "name": "04_STRATEGY_GOVERNANCE",
        "title": "Strategy & Governance",
        "description": "Roadmap strategiche, piani industriali, OKR, budget annuali e pitch deck",
    },
    "05_COMMERCIAL_GTM": {
        "code": "05",
        "name": "05_COMMERCIAL_GTM",
        "title": "Commercial & Go-To-Market",
        "description": "Preventivi, offerte commerciali, pipeline CRM, clienti attivi e listini",
    },
    "06_PRODUCT_RESEARCH": {
        "code": "06",
        "name": "06_PRODUCT_RESEARCH",
        "title": "Product & Research",
        "description": "Specifiche funzionali, PRD, user story, concept notebook e documentazione",
    },
    "07_ENGINEERING_INFRA": {
        "code": "07",
        "name": "07_ENGINEERING_INFRA",
        "title": "Engineering & Infrastructure",
        "description": "Architettura software, diagrammi, repository, configurazioni cloud e CI/CD",
    },
    "08_ASSETS_BRAND": {
        "code": "08",
        "name": "08_ASSETS_BRAND",
        "title": "Assets & Brand",
        "description": "Brand identity, loghi, asset multimediali, design system e materiali grafici",
    },
    "09_MANAGEMENT_MEMORY": {
        "code": "09",
        "name": "09_MANAGEMENT_MEMORY",
        "title": "Management Memory",
        "description": "Verbali di assemblea, verbali CDA, decision log e delibere fondatore",
    },
    "10_OPERATIONS_RECORDS": {
        "code": "10",
        "name": "10_OPERATIONS_RECORDS",
        "title": "Operations Records & Ledger",
        "description": "Audit trail immutabile, log operativi, transazioni e registri di esecuzione",
    },
    "99_ARCHIVE": {
        "code": "99",
        "name": "99_ARCHIVE",
        "title": "Archive & Deprecated",
        "description": "Documenti storici superati, vecchie versioni e materiale archiviato",
    },
}


def normalize_domain_key(domain_input: str) -> str:
    """Riconduce qualsiasi codice o nome (es. '01', '01_CORPORATE', 'corporate') alla chiave canonica."""
    normalized = domain_input.strip().upper()
    
    # 1. Match esatto con chiave canonica
    if normalized in CANONICAL_DOMAINS:
        return normalized
        
    # 2. Match su prefisso numerico a due cifre (es. '01', '1', '01_...')
    for key, info in CANONICAL_DOMAINS.items():
        if normalized == info["code"] or normalized == str(int(info["code"])):
            return key
        if normalized.startswith(f"{info['code']}_"):
            return key
            
    # 3. Match su parole chiave nel nome
    for key in CANONICAL_DOMAINS:
        tokens = key.split("_")
        for token in tokens[1:]:
            if token and token in normalized:
                return key
                
    # Fallback su operations records o corporate
    return "10_OPERATIONS_RECORDS"


class StorageItem(BaseModel):
    """Metadato canonico di un file o directory memorizzato in un provider di storage."""
    item_id: str = Field(..., description="Identificativo univoco remoto (es. Google Drive File ID, S3 Key, path locale)")
    name: str = Field(..., description="Nome file o directory (es. 'BILANCIO_2025.pdf')")
    path: str = Field(..., description="Percorso logico relativo al dominio o alla root (es. '02_FINANCE_LEGAL/bilanci/2025.pdf')")
    domain: str = Field(default="00_INDEX_RULES", description="Dominio persistente canonico associato")
    is_directory: bool = Field(default=False, description="Flag directory o file")
    size_bytes: int = Field(default=0, ge=0, description="Dimensione in byte")
    mime_type: str = Field(default="application/octet-stream", description="MIME type IANA")
    modified_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp ultima modifica")
    sha256_hash: Optional[str] = Field(default=None, description="Checksum SHA256 per versioning e deduplica")
    version_fingerprint: str = Field(default="", description="Impronta rapida versione (modifiedTime + size)")
    provider: StorageProvider = Field(..., description="Provider fisico dello storage")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Attributi proprietari del provider")

    def model_post_init(self, __context: Any) -> None:
        if not self.version_fingerprint:
            raw = f"{self.item_id}:{self.size_bytes}:{self.modified_time.isoformat()}"
            self.version_fingerprint = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class DomainFolderMap(BaseModel):
    """Mappatura logica dei 10 domini sulle cartelle o prefissi remoti dello storage."""
    workspace_id: str
    provider: StorageProvider
    root_reference: str = Field(..., description="ID cartella root Drive, bucket S3 o path locale")
    domain_references: Dict[str, str] = Field(default_factory=dict, description="Mappa dominio canonico -> ID cartella / prefisso remoto")
    last_synced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BaseStorageAdapter(abc.ABC):
    """Contratto astratto per connettori di storage multi-cloud."""

    def __init__(self, workspace_id: str, provider: StorageProvider, storage_config: Dict[str, Any]):
        self.workspace_id = workspace_id
        self.provider = provider
        self.storage_config = storage_config

    @abc.abstractmethod
    async def ensure_domains_exist(self) -> DomainFolderMap:
        """Verifica o inizializza le cartelle dei 10 domini persistenti nello storage remoto."""
        pass

    @abc.abstractmethod
    async def list_items(
        self,
        domain: Optional[str] = None,
        subpath: str = "",
        recursive: bool = False,
        force_refresh: bool = False,
    ) -> List[StorageItem]:
        """Elenca i file e le cartelle per dominio o percorso."""
        pass

    @abc.abstractmethod
    async def get_item(self, item_id_or_path: str) -> Optional[StorageItem]:
        """Recupera i metadati di un singolo elemento."""
        pass

    @abc.abstractmethod
    async def read_content(self, item_id_or_path: str) -> bytes:
        """Legge il payload binario di un file."""
        pass

    @abc.abstractmethod
    async def write_content(
        self,
        domain: str,
        filename: str,
        content: bytes,
        subpath: str = "",
        mime_type: str = "text/plain",
    ) -> StorageItem:
        """Scrive un nuovo file o aggiorna un file esistente nel dominio specificato."""
        pass

    @abc.abstractmethod
    async def delete_item(self, item_id_or_path: str) -> bool:
        """Rimuove un file dallo storage."""
        pass

    @abc.abstractmethod
    async def get_domain_fingerprint(self, domain: str) -> str:
        """Restituisce un hash compatto che muta se un qualsiasi file nel dominio cambia."""
        pass
