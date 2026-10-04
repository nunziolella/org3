"""Org 3.0 Core Ontology: Organizations, Divisions, Roles, Agents and Persistent Information Mapping.

Invarianti dal Persistent Information Layer (AIPROD 03_MEMORY_SYSTEM):
1. Lo storage fisico risponde a: 'Che tipo di informazione è?' (10 domini funzionali).
2. Org3 risponde a: 'Chi, in quale ruolo, funzione, divisione ha prodotto o accede a questa informazione?'
3. Nessuna duplicazione fisica: ruoli e divisioni sono dimensioni di retrieval e permission.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FunctionalDomain(str, Enum):
    """I 10 Domini Funzionali Canonici + Regole e Archivio dal Persistent Information Layer."""
    D00_INDEX_RULES = "00_INDEX_RULES"
    D01_CORPORATE = "01_CORPORATE"
    D02_STRATEGY = "02_STRATEGY"
    D03_ORGANIZATION_GOVERNANCE = "03_ORGANIZATION_GOVERNANCE"
    D04_ADMINISTRATION_FINANCE = "04_ADMINISTRATION_FINANCE"
    D05_TECHNOLOGY_DATA = "05_TECHNOLOGY_DATA"
    D06_PRODUCT = "06_PRODUCT"
    D07_MARKET_COMMERCIAL = "07_MARKET_COMMERCIAL"
    D08_RESEARCH_KNOWLEDGE = "08_RESEARCH_KNOWLEDGE"
    D09_MANAGEMENT_MEMORY = "09_MANAGEMENT_MEMORY"
    D10_OPERATIONS_RECORDS = "10_OPERATIONS_RECORDS"
    D99_ARCHIVE = "99_ARCHIVE"


class MemoryAuthority(str, Enum):
    """I 5 Livelli di Autorità di Memoria (MEMORY_REGISTRY)."""
    RAW_MEMORY = "raw_memory"            # Dati sorgente non interpretati
    META_MEMORY = "meta_memory"          # Indici, registri, id stabili, routing
    CANONICAL_MEMORY = "canonical_memory"# Verità approvata attuale dell'azienda
    DECISION_MEMORY = "decision_memory"  # Record immutabile di scelte e motivazioni
    OPERATIONAL_MEMORY = "operational_memory" # Tracce di esecuzione e dossier WP


class DocumentLifecycleStatus(str, Enum):
    """Stato di ciclo di vita dell'informazione persistente."""
    RAW = "RAW"                          # Sorgente acquisita, non interpretata
    WORKING = "WORKING"                  # In lavorazione attiva nel dossier
    OUTPUT = "OUTPUT"                    # Artefatto completato dal lavoro
    REVIEWED = "REVIEWED"                # Revisione di qualità o fattuale completata
    APPROVED_CANONICAL = "APPROVED_CANONICAL" # Stato attuale autorevole approvato
    SUPERSEDED = "SUPERSEDED"            # Storicamente rilevante ma non più corrente
    ARCHIVED = "ARCHIVED"                # Conservato senza autorità attiva


class OrgStructureType(str, Enum):
    """Modelli organizzativi supportati in Org3."""
    FUNCTIONAL = "FUNCTIONAL"
    DIVISIONAL = "DIVISIONAL"
    MATRIX = "MATRIX"


class AgentType(str, Enum):
    """Tipologia di attore nel sistema MAS."""
    HUMAN = "HUMAN"
    AI_SYSTEM = "AI_SYSTEM"
    AI_SUBAGENT = "AI_SUBAGENT"
    WORKER_SERVICE = "WORKER_SERVICE"


class ActionPermission(BaseModel):
    """Permesso atomico su risorsa ed azione."""
    resource: str                        # es. "commercial_proposal", "strategy_core", "code_repository"
    action: str                          # "read", "create_draft", "publish", "execute", "delegate"
    scope: Optional[str] = None          # es. "division:qubitdata", "domain:07_MARKET_COMMERCIAL"


class Role(BaseModel):
    """Definizione canonica di un Ruolo in Org3."""
    id: str                              # es. "ROLE_FOUNDER_CEO", "ROLE_TECH_LEAD", "ROLE_OPERATOR"
    name: str
    department_level: str                # es. "L0_GOVERNANCE", "L1_STRATEGY_UX", "L2_TECH_SDLC"
    description: str
    permissions: List[ActionPermission] = Field(default_factory=list)
    decision_rights: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    is_management_role: bool = False


class Agent(BaseModel):
    """Attore reale (umano o artificiale) che interpreta uno o più ruoli."""
    id: str                              # es. "agent-nunzio", "agent-antigravity", "agent-francesco"
    name: str
    agent_type: AgentType
    email: Optional[str] = None
    assigned_roles: List[str] = Field(default_factory=list)  # Lista di role_id
    division_ids: List[str] = Field(default_factory=list)    # Divisioni in cui opera
    is_master: bool = False             # Master Assoluto (God Mode: bypass controlli ordinari)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Division(BaseModel):
    """Divisione di business o linea operativa (es. Symbiotic Core, Qubitdata)."""
    id: str                              # es. "DIV_SYMBIOTIC_CORE", "DIV_QUBITDATA"
    name: str
    code: str                            # es. "SYM", "QD"
    lead_agent_id: Optional[str] = None
    description: str = ""


class OrganizationalUnit(BaseModel):
    """Unità o funzione organizzativa (es. Engineering, Marketing, Finance)."""
    id: str
    name: str
    domain: FunctionalDomain
    division_id: Optional[str] = None
    lead_role_id: Optional[str] = None
    members_count: int = 0


class PersistentArtifactReference(BaseModel):
    """Riferimento tipizzato a un artefatto persistente nel Persistent Information Layer."""
    id: str                              # es. "art-94b2f10"
    canonical_id: str                    # es. "QD-STR-001", "WP-01_CALL_0_RECORD"
    domain: FunctionalDomain             # 01..10
    authority: MemoryAuthority           # raw, meta, canonical, decision, operational
    status: DocumentLifecycleStatus      # RAW..APPROVED_CANONICAL..ARCHIVED
    storage_path: str                    # Path in Google Drive / S:/ virtuale
    title: str
    created_by_agent_id: str
    created_under_role_id: str
    division_id: Optional[str] = None
    hash_sha256: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)
