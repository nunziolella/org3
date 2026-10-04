# Org 3.0 (Org3) — Multi-Agent Operating Framework

[![Test Suite](https://img.shields.io/badge/pytest-11%20passed-brightgreen.svg)](tests/)
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue.svg)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **"Il contratto di delega ideale tra umano e macchina: le regole le scrive il Founder, le macchine le eseguono."**  
> — Dottrina Fondativa Org3 (10/07/2026)

Org3 è un framework Python open source agnostico e portabile per modellare, governare e far cooperare team ibridi di umani e agenti AI in un'organizzazione autonoma (Multi-Agent System).

Org3 sta a **Structura** come Git sta a GitHub: è il framework/engine di governance e modello organizzativo sottostante, mentre Structura ne è la piattaforma di gestione operativa, interfaccia utente e cockpit gestionale.

---

## 🏛️ I Quattro Piani di Separazione

Allineato alla specifica sovrana del **Persistent Information Layer** (`03_MEMORY_SYSTEM`):

1. **Organizational Model (Org3):** definisce Unità, Divisioni, Funzioni, Ruoli, Agenti (Human / AI), permessi IAM, responsabilità, contratti di delega ed escalation.
2. **Management & Execution Plane (Structura / PM):** gestisce la gerarchia di pianificazione (`Macro → Objective/KR → Initiative → Epic → Milestone → Story → Task`) e il `Research Lab` scientifico.
3. **Persistent Information Layer (Drive / Object Storage):** archiviazione duratura strutturata sui 10 domini canonici.
4. **Retrieval & Memory Intelligence (Memograph):** knowledge graph, calcolo del lignaggio e 5 livelli di autorità mnemonica (`raw_memory`, `meta_memory`, `canonical_memory`, `decision_memory`, `operational_memory`).

---

## 🔑 Caratteristiche Principali

### 1. Ontologia Multi-Dimensionale (`org3.core.ontology`)
- **Nessuna duplicazione di file fisici:** Lo storage fisico risponde a *"Che tipo di informazione è?"* (10 domini: `01_CORPORATE` .. `10_OPERATIONS_RECORDS`). Org3 risponde a *"Chi, con quale ruolo o divisione vi accede?"*.
- **Attori MAS:** Supporto nativo per `HUMAN`, `AI_SYSTEM`, `AI_SUBAGENT`, `WORKER_SERVICE`.
- **Master Assoluto:** Gestione del God Mode per il Founder (`is_master=True`), che scavalca i vincoli burocratici ordinari garantendo flessibilità massima.

### 2. Delegation Policy Engine (`org3.core.delegation`)
Risolve formalmente i conflitti di attribuzione e sovra-estensione (es. **caso CHRIMAT**):
- Contratti espliciti `DelegationPolicy` che vincolano le azioni delegate (es. proposte commerciali, NDA, trattative).
- Vincoli negativi categorici:
  - `NO_IP_CONCESSION`: Blocco immediato di qualsiasi cessione o licenza esclusiva di Proprietà Intellettuale.
  - `NO_EXCLUSIVITY`: Divieto di concessione di patti di esclusiva commerciale o territoriale.
  - `NO_ROADMAP_COMMITMENT`: Divieto di impegnare date fisse di roadmap non concordate.
  - `MAX_DISCOUNT_PERCENT`: Tetto massimo di sconto (es. max 10%).
  - `MAX_FINANCIAL_AMOUNT`: Soffitto finanziario per singola operazione.

### 3. Matrice di Rischio e Governance Gates (`org3.core.governance_gates`)
Classificazione formale delle mutazioni operative:
- **Classe A (Auto-approve):** Note interne, metadati, modifiche cosmetiche a basso rischio.
- **Classe B (Evidence-backed):** Chiusura task approvata automaticamente solo in presenza di evidenza oggettiva verificabile (commit, deploy, test verde).
- **Classe C (Human-in-the-Loop):** Mutazioni ad alto impatto (creazione obiettivi, cambio scope, invio offerte commerciali) con escalation [HITL].
- **Classe D (Master Assoluto Change Control):** Invarianti hard, ontologia, schema governance, riservati al Founder.

### 4. Virtual Memory Lenses (`org3.core.views`)
Generatore di proiezioni mnemoniche virtuali:
- Ricostruisce al volo viste specializzate (es. `CFO Memory View`, `Technology Memory View`, `Division Dossier`) aggregando artefatti canonici, evidenze e decisioni senza copiare file.

### 5. Cognitive CI/CD & Zero-Vulnerability (`org3.core.gates`)
- Analizzatore AST Python per intercettare chiamate pericolose (`eval`, `exec`, shell non sanitizzate) prima del merge.

---

## 🚀 Quickstart

### Installazione
```bash
git clone https://github.com/nunziolella/org3.git
cd org3
pip install -e .
```

### Utilizzo CLI
```bash
# Elenca i 10 domini canonici del Persistent Information Layer
org3 list-domains

# Esegui il test di validazione delega (Caso CHRIMAT)
org3 test-chrimat-delegation

# Esegui l'audit di sicurezza AST del codice
org3 audit-security .
```

### Utilizzo in Python
```python
from org3 import (
    Role, Agent, AgentType, DelegationPolicy, 
    DelegationConstraint, DelegationConstraintType, DelegationEngine
)

# 1. Definizione della policy di delega
policy = DelegationPolicy(
    id="del-partner-001",
    delegator_id="agent-nunzio",
    delegate_id="agent-francesco",
    allowed_actions=["send_commercial_proposal"],
    constraints=[
        DelegationConstraint(constraint_type=DelegationConstraintType.NO_IP_CONCESSION),
        DelegationConstraint(constraint_type=DelegationConstraintType.MAX_DISCOUNT_PERCENT, value=10.0),
    ],
    financial_ceiling=25000.0
)

# 2. Valutazione di un'operazione tentata
result = DelegationEngine.evaluate_action(
    policy=policy,
    requested_action="send_commercial_proposal",
    financial_amount=18000.0,
    context_payload={"concedes_ip": False, "discount_percent": 8.0}
)

assert result.allowed is True
```

---

## 🧪 Test Suite

Tutti i test sono implementati con `pytest`:
```bash
pytest tests/
```
Esito attuale: **11/11 tests passati (100% SUCCESS)**.
