"""Org3 Multi-Tenant & Governance Data Contracts.

Invarianti:
1. Namespace isolato: Tabelle e modelli rispecchiano le entità di piattaforma (org3_*).
2. Non-contaminazione: Nessun accoppiamento con logica di esecuzione o preventivazione specifica di Structura.
3. Master Assoluto: Nunzio Lella ha sempre is_master=True, garantendo bypass dei filtri RBAC ordinari.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class PlanType(str, Enum):
    """Piani di abbonamento Org3 Platform."""
    FREE = "free"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class StorageProvider(str, Enum):
    """Provider cloud di storage agnostico."""
    GOOGLE_DRIVE = "google_drive"
    S3 = "s3"
    R2 = "r2"
    LOCAL_FS = "local_fs"


class MemberType(str, Enum):
    """Tipologia di entità agente censita nel sistema."""
    HUMAN = "HUMAN"
    AI_SYSTEM = "AI_SYSTEM"
    WORKER_SERVICE = "WORKER_SERVICE"


class MemberRole(str, Enum):
    """Ruoli gerarchici standard in Org3."""
    FOUNDER_GODMODE = "FOUNDER_GODMODE"
    CEO = "CEO"
    VP = "VP"
    TECH_LEAD = "TECH_LEAD"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


class ApprovalStatus(str, Enum):
    """Stato della richiesta Human-in-the-Loop."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class Organization(BaseModel):
    """Organizzazione / Tenant primario."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    slug: str = Field(..., max_length=64, description="Slug univoco tenant (es. 'qubitdata', 'symbiotic')")
    name: str = Field(..., max_length=255, description="Ragione sociale o nome azienda")
    plan: PlanType = Field(default=PlanType.FREE)
    owner_email: str = Field(..., max_length=255)
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Workspace(BaseModel):
    """Workspace di lavoro e storage associato a un'organizzazione."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    name: str = Field(..., max_length=255)
    storage_provider: StorageProvider = Field(default=StorageProvider.GOOGLE_DRIVE)
    storage_config: Dict[str, Any] = Field(default_factory=dict, description="Parametri provider (folder_id, bucket)")
    is_primary: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Member(BaseModel):
    """Membro del team (umano, agente AI o worker)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    email: str = Field(..., max_length=255)
    name: str = Field(..., max_length=255)
    member_type: MemberType = Field(default=MemberType.HUMAN)
    role: MemberRole = Field(default=MemberRole.OPERATOR)
    is_master: bool = Field(default=False, description="God Mode per Nunzio Lella")
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DelegationPolicyRecord(BaseModel):
    """Contratto di delega persistito su Neon PostgreSQL."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    actor_id: UUID
    name: str = Field(..., max_length=255)
    scope: str = Field(..., max_length=128)
    max_financial_authority: float = Field(default=0.00, ge=0.0)
    constraints: List[str] = Field(default_factory=list, description="es. ['NO_IP_CONCESSION', 'NO_EXCLUSIVITY']")
    approval_gate: str = Field(default="CLASS_C", description="CLASS_A, CLASS_B, CLASS_C, CLASS_D")
    is_revoked: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApprovalRequest(BaseModel):
    """Richiesta di approvazione Human-in-the-Loop emessa verso Org3 Hub."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    source_service: str = Field(default="structura", max_length=64)
    risk_class: str = Field(default="C", max_length=8)
    title: str = Field(..., max_length=255)
    description: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    requested_by: Optional[UUID] = None
    status: ApprovalStatus = Field(default=ApprovalStatus.PENDING)
    resolution_note: Optional[str] = None
    resolved_by: Optional[UUID] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApiToken(BaseModel):
    """Token di connessione e autenticazione Org3 Connect."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    member_id: UUID
    token_hash: str = Field(..., max_length=128)
    name: str = Field(..., max_length=255)
    allowed_scopes: List[str] = Field(default_factory=lambda: ["read", "write"])
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
