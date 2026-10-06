"""Router for Organization (Tenant) and Workspace management in Org3 Platform."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from org3.api.db import get_db
from org3.models.multitenant import Organization, PlanType, StorageProvider, Workspace

router = APIRouter(prefix="/v1", tags=["Organizations & Workspaces"])


class CreateOrganizationRequest(BaseModel):
    slug: str = Field(..., max_length=64, description="Slug URL-safe univoco (es. 'qubitdata')")
    name: str = Field(..., max_length=255, description="Nome dell'azienda")
    owner_email: str = Field(..., max_length=255)
    plan: PlanType = Field(default=PlanType.FREE)


class UpdateOrganizationRequest(BaseModel):
    name: Optional[str] = None
    plan: Optional[PlanType] = None
    is_active: Optional[bool] = None


class CreateWorkspaceRequest(BaseModel):
    name: str = Field(..., max_length=255)
    storage_provider: StorageProvider = Field(default=StorageProvider.GOOGLE_DRIVE)
    storage_config: Dict[str, Any] = Field(default_factory=dict)
    is_primary: bool = False


@router.post("/organizations", response_model=Organization, status_code=status.HTTP_201_CREATED)
def create_organization(req: CreateOrganizationRequest, db=Depends(get_db)):
    """Crea una nuova organizzazione / tenant sulla piattaforma Org3."""
    cur = db.cursor()
    # Verifica unicità slug
    cur.execute("SELECT id FROM org3_organizations WHERE slug = %s;", (req.slug.lower().strip(),))
    if cur.fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Organizzazione con slug '{req.slug}' già esistente."
        )

    cur.execute(
        """
        INSERT INTO org3_organizations (slug, name, owner_email, plan)
        VALUES (%s, %s, %s, %s)
        RETURNING id, slug, name, plan, owner_email, is_active, created_at, updated_at;
    """,
        (req.slug.lower().strip(), req.name.strip(), req.owner_email.strip(), req.plan.value),
    )
    row = cur.fetchone()
    # OUTBOX EVENT
    cur.execute(
        "INSERT INTO org3_outbox (aggregate_type, aggregate_id, event_type, payload) VALUES (%s, %s, %s, %s);",
        ('ORGANIZATION', str(row['id']), 'ORGANIZATION_CREATED', json.dumps(dict(row), default=str))
    )
    return Organization(**dict(row))


@router.get("/organizations", response_model=List[Organization])
def list_organizations(plan: Optional[PlanType] = None, is_active: Optional[bool] = None, db=Depends(get_db)):
    """Elenca le organizzazioni registrate."""
    cur = db.cursor()
    query = "SELECT id, slug, name, plan, owner_email, is_active, created_at, updated_at FROM org3_organizations WHERE 1=1"
    params = []
    if plan is not None:
        query += " AND plan = %s"
        params.append(plan.value)
    if is_active is not None:
        query += " AND is_active = %s"
        params.append(is_active)
    query += " ORDER BY created_at DESC;"

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    return [Organization(**dict(r)) for r in rows]


@router.get("/organizations/{id_or_slug}", response_model=Organization)
def get_organization(id_or_slug: str, db=Depends(get_db)):
    """Recupera un'organizzazione tramite UUID o slug univoco."""
    cur = db.cursor()
    is_uuid = False
    try:
        UUID(id_or_slug)
        is_uuid = True
    except ValueError:
        is_uuid = False

    if is_uuid:
        cur.execute(
            "SELECT id, slug, name, plan, owner_email, is_active, created_at, updated_at FROM org3_organizations WHERE id = %s;",
            (id_or_slug,),
        )
    else:
        cur.execute(
            "SELECT id, slug, name, plan, owner_email, is_active, created_at, updated_at FROM org3_organizations WHERE slug = %s;",
            (id_or_slug.lower().strip(),),
        )

    row = cur.fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organizzazione '{id_or_slug}' non trovata."
        )
    return Organization(**dict(row))


@router.patch("/organizations/{org_id}", response_model=Organization)
def update_organization(org_id: str, req: UpdateOrganizationRequest, db=Depends(get_db)):
    """Aggiorna le informazioni o il piano di un'organizzazione."""
    cur = db.cursor()
    cur.execute("SELECT id FROM org3_organizations WHERE id = %s;", (org_id,))
    if not cur.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizzazione non trovata.")

    updates = []
    params = []
    if req.name is not None:
        updates.append("name = %s")
        params.append(req.name.strip())
    if req.plan is not None:
        updates.append("plan = %s")
        params.append(req.plan.value)
    if req.is_active is not None:
        updates.append("is_active = %s")
        params.append(req.is_active)

    if not updates:
        return get_organization(org_id, db)

    updates.append("updated_at = NOW()")
    params.append(org_id)
    query = f"UPDATE org3_organizations SET {', '.join(updates)} WHERE id = %s RETURNING id, slug, name, plan, owner_email, is_active, created_at, updated_at;"
    cur.execute(query, tuple(params))
    row = cur.fetchone()
    # OUTBOX EVENT
    cur.execute(
        "INSERT INTO org3_outbox (aggregate_type, aggregate_id, event_type, payload) VALUES (%s, %s, %s, %s);",
        ('ORGANIZATION', str(row['id']), 'ORGANIZATION_UPDATED', json.dumps(dict(row), default=str))
    )
    return Organization(**dict(row))


@router.post("/organizations/{org_id}/workspaces", response_model=Workspace, status_code=status.HTTP_201_CREATED)
def create_workspace(org_id: str, req: CreateWorkspaceRequest, db=Depends(get_db)):
    """Crea un nuovo workspace collegato all'organizzazione e al suo storage cloud."""
    cur = db.cursor()
    cur.execute("SELECT id FROM org3_organizations WHERE id = %s;", (org_id,))
    if not cur.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizzazione non trovata.")

    cur.execute(
        """
        INSERT INTO org3_workspaces (org_id, name, storage_provider, storage_config, is_primary)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, org_id, name, storage_provider, storage_config, is_primary, created_at;
    """,
        (
            org_id,
            req.name.strip(),
            req.storage_provider.value,
            json.dumps(req.storage_config),
            req.is_primary,
        ),
    )
    row = cur.fetchone()
    return Workspace(**dict(row))


@router.get("/organizations/{org_id}/workspaces", response_model=List[Workspace])
def list_workspaces(org_id: str, db=Depends(get_db)):
    """Elenca tutti i workspace di un'organizzazione."""
    cur = db.cursor()
    cur.execute(
        """
        SELECT id, org_id, name, storage_provider, storage_config, is_primary, created_at
        FROM org3_workspaces
        WHERE org_id = %s
        ORDER BY is_primary DESC, created_at ASC;
    """,
        (org_id,),
    )
    rows = cur.fetchall()
    return [Workspace(**dict(r)) for r in rows]
