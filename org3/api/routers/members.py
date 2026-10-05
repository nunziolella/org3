"""Router for Directory, Personas, and IAM Members in Org3 Platform."""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from org3.api.db import get_db
from org3.models.multitenant import Member, MemberRole, MemberType

router = APIRouter(prefix="/v1", tags=["Members & IAM"])


class AddMemberRequest(BaseModel):
    email: str = Field(..., max_length=255)
    name: str = Field(..., max_length=255)
    member_type: MemberType = Field(default=MemberType.HUMAN)
    role: MemberRole = Field(default=MemberRole.OPERATOR)
    is_master: bool = Field(default=False, description="True solo per Nunzio Lella (God Mode)")


class UpdateMemberRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[MemberRole] = None
    member_type: Optional[MemberType] = None
    is_master: Optional[bool] = None
    is_active: Optional[bool] = None


@router.post("/organizations/{org_id}/members", response_model=Member, status_code=status.HTTP_201_CREATED)
def add_member(org_id: str, req: AddMemberRequest, db=Depends(get_db)):
    """Aggiunge un collaboratore umano, un agente AI o un worker all'organizzazione."""
    cur = db.cursor()
    # Verifica esistenza organizzazione
    cur.execute("SELECT id FROM org3_organizations WHERE id = %s;", (org_id,))
    if not cur.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizzazione non trovata.")

    # Controllo unicità email per org
    cur.execute("SELECT id FROM org3_members WHERE org_id = %s AND email = %s;", (org_id, req.email.strip().lower()))
    if cur.fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Membro con email '{req.email}' già presente nell'organizzazione."
        )

    # Invariante Master Assoluto: solo l'email del Founder può avere is_master=True
    is_master_final = req.is_master
    if is_master_final and req.email.strip().lower() != "01nunzio.lella@gmail.com":
        # Se non è Nunzio, non può avere God Mode
        is_master_final = False

    cur.execute(
        """
        INSERT INTO org3_members (org_id, email, name, member_type, role, is_master)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, org_id, email, name, member_type, role, is_master, is_active, created_at;
    """,
        (
            org_id,
            req.email.strip().lower(),
            req.name.strip(),
            req.member_type.value,
            req.role.value,
            is_master_final,
        ),
    )
    row = cur.fetchone()
    return Member(**dict(row))


@router.get("/organizations/{org_id}/members", response_model=List[Member])
def list_members(org_id: str, member_type: Optional[MemberType] = None, role: Optional[MemberRole] = None, db=Depends(get_db)):
    """Elenca i membri di un'organizzazione (umani, agenti AI, worker)."""
    cur = db.cursor()
    query = """
        SELECT id, org_id, email, name, member_type, role, is_master, is_active, created_at
        FROM org3_members
        WHERE org_id = %s
    """
    params = [org_id]
    if member_type is not None:
        query += " AND member_type = %s"
        params.append(member_type.value)
    if role is not None:
        query += " AND role = %s"
        params.append(role.value)
    query += " ORDER BY is_master DESC, created_at ASC;"

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    return [Member(**dict(r)) for r in rows]


@router.get("/members/{member_id}", response_model=Member)
def get_member(member_id: str, db=Depends(get_db)):
    """Recupera le informazioni di un membro tramite il suo ID."""
    cur = db.cursor()
    cur.execute(
        """
        SELECT id, org_id, email, name, member_type, role, is_master, is_active, created_at
        FROM org3_members
        WHERE id = %s;
    """,
        (member_id,),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membro non trovato.")
    return Member(**dict(row))


@router.patch("/members/{member_id}", response_model=Member)
def update_member(member_id: str, req: UpdateMemberRequest, db=Depends(get_db)):
    """Aggiorna ruolo, stato o permessi di un membro."""
    cur = db.cursor()
    cur.execute("SELECT id, email FROM org3_members WHERE id = %s;", (member_id,))
    existing = cur.fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membro non trovato.")

    updates = []
    params = []
    if req.name is not None:
        updates.append("name = %s")
        params.append(req.name.strip())
    if req.role is not None:
        updates.append("role = %s")
        params.append(req.role.value)
    if req.member_type is not None:
        updates.append("member_type = %s")
        params.append(req.member_type.value)
    if req.is_master is not None:
        # Solo l'email di Nunzio può avere God Mode
        if req.is_master and existing["email"] != "01nunzio.lella@gmail.com":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="God Mode riservato esclusivamente al Founder.")
        updates.append("is_master = %s")
        params.append(req.is_master)
    if req.is_active is not None:
        updates.append("is_active = %s")
        params.append(req.is_active)

    if not updates:
        return get_member(member_id, db)

    params.append(member_id)
    query = f"UPDATE org3_members SET {', '.join(updates)} WHERE id = %s RETURNING id, org_id, email, name, member_type, role, is_master, is_active, created_at;"
    cur.execute(query, tuple(params))
    return Member(**dict(cur.fetchone()))
