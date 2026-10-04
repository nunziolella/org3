"""Org 3.0 Virtual Memory Views & Lens Engine.

Attua il principio del Persistent Information Layer:
'Lo storage fisico risponde a *cosa è l'informazione*.
 Org3 risponde a *chi, in quale ruolo o divisione la produce o la usa*.
 Nessun file viene duplicato: le memorie per ruolo (es. CFO Memory, Technology Dossier)
 o per divisione sono viste virtuali proiettate attraverso relazioni e permessi IAM.'
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from org3.core.ontology import (
    FunctionalDomain,
    MemoryAuthority,
    DocumentLifecycleStatus,
    Role,
    Agent,
    PersistentArtifactReference
)


class VirtualMemoryView(BaseModel):
    """Proiezione virtuale di memoria ricostruita senza duplicazione di file fisici."""
    view_name: str
    target_role_id: Optional[str] = None
    target_division_id: Optional[str] = None
    canonical_documents: List[PersistentArtifactReference] = Field(default_factory=list)
    operational_records: List[PersistentArtifactReference] = Field(default_factory=list)
    decisions: List[PersistentArtifactReference] = Field(default_factory=list)
    research_knowledge: List[PersistentArtifactReference] = Field(default_factory=list)
    total_artifacts_count: int = 0


class VirtualMemoryLens:
    """Motore di calcolo delle viste virtuali della memoria aziendale."""

    @staticmethod
    def build_view(
        view_name: str,
        artifacts: List[PersistentArtifactReference],
        role: Optional[Role] = None,
        division_id: Optional[str] = None,
        canonical_only: bool = False
    ) -> VirtualMemoryView:
        """Costruisce una vista virtuale aggregata filtrando e categorizzando gli artefatti."""
        canonicals: List[PersistentArtifactReference] = []
        operations: List[PersistentArtifactReference] = []
        decisions: List[PersistentArtifactReference] = []
        research: List[PersistentArtifactReference] = []

        for art in artifacts:
            # 1. Filtro per divisione se specificato (salvo documenti trasversali senza divisione o a scope globale)
            if division_id and art.division_id and art.division_id != division_id:
                continue

            # 2. Se canonical_only è richiesto, considera solo la memoria canonica valida
            if canonical_only:
                if art.authority == MemoryAuthority.CANONICAL_MEMORY and art.status == DocumentLifecycleStatus.APPROVED_CANONICAL:
                    canonicals.append(art)
                continue

            # 3. Categorizzazione negli assi della vista
            if art.authority == MemoryAuthority.CANONICAL_MEMORY:
                if art.status in (DocumentLifecycleStatus.APPROVED_CANONICAL, DocumentLifecycleStatus.REVIEWED):
                    canonicals.append(art)
            elif art.authority == MemoryAuthority.DECISION_MEMORY:
                decisions.append(art)
            elif art.authority == MemoryAuthority.OPERATIONAL_MEMORY:
                operations.append(art)
            elif art.domain == FunctionalDomain.D08_RESEARCH_KNOWLEDGE:
                research.append(art)
            elif art.authority == MemoryAuthority.RAW_MEMORY:
                # RAW rimane collegato come evidenza operativa
                operations.append(art)

        total = len(canonicals) + len(operations) + len(decisions) + len(research)

        return VirtualMemoryView(
            view_name=view_name,
            target_role_id=role.id if role else None,
            target_division_id=division_id,
            canonical_documents=canonicals,
            operational_records=operations,
            decisions=decisions,
            research_knowledge=research,
            total_artifacts_count=total
        )

    @classmethod
    def build_cfo_memory(
        cls,
        artifacts: List[PersistentArtifactReference],
        division_id: Optional[str] = None
    ) -> VirtualMemoryView:
        """Costruisce la vista specializzata 'CFO Memory' (Amministrazione, Finanza, Contratti e Scelte Economiche)."""
        finance_artifacts = [
            a for a in artifacts
            if a.domain in (FunctionalDomain.D04_ADMINISTRATION_FINANCE, FunctionalDomain.D01_CORPORATE)
            or "finance" in a.canonical_id.lower() or "cfo" in a.metadata.get("tags", [])
        ]
        return cls.build_view(
            view_name="CFO Memory View",
            artifacts=finance_artifacts,
            division_id=division_id
        )

    @classmethod
    def build_tech_memory(
        cls,
        artifacts: List[PersistentArtifactReference],
        division_id: Optional[str] = None
    ) -> VirtualMemoryView:
        """Costruisce la vista specializzata 'Technology Memory' (Architetture, SDLC, Asset Tecnici e Standard)."""
        tech_artifacts = [
            a for a in artifacts
            if a.domain in (FunctionalDomain.D05_TECHNOLOGY_DATA, FunctionalDomain.D06_PRODUCT)
            or "tech" in a.canonical_id.lower() or "architecture" in a.metadata.get("tags", [])
        ]
        return cls.build_view(
            view_name="Technology & Product Memory View",
            artifacts=tech_artifacts,
            division_id=division_id
        )
