# plan.md — iProd OS (MemoGraph OS)

## 1) Objectives
- Deliver a premium AI-first personal OS MVP that turns brain-dumps into structured items (task/project/idea/note/problem/goal), prioritizes them, and guides “what to do now”.
- Prove the **core workflow** in isolation: multi-provider LLM classification + weekly review generation returning **strict structured JSON**.
- Build V1 app (React + FastAPI + MongoDB) around the proven core: Inbox → AI suggestions → convert to Projects/Tasks/Incubator → Next Actions focus → Weekly Review.
- Include i18n (IT/EN), real voice transcription (Web Speech API), and a Settings page for BYOK AI providers + Emergent built-in default.

## 2) Implementation Steps

### Phase 1 — Core POC (Isolation: AI Assist + Review)
**User stories (POC)**
1. As a user, I can paste a messy brain dump and get a structured JSON classification I can trust.
2. As a user, I can see a suggested Area, priority inputs, and a concrete next action for each brain dump.
3. As a user, I can distinguish whether something should become an Active Project or go to the Incubator.
4. As a user, I can run a weekly review summary that highlights blockers and what to freeze/delegate.
5. As a developer, I can swap AI providers (Emergent default vs BYOK key) without changing app logic.

**Steps**
1. Websearch best practices for: (a) strict JSON LLM outputs, (b) provider abstraction, (c) retry/validation patterns.
2. Define the **LLM JSON schema** for `classify_inbox` and `generate_weekly_review` (Pydantic models; forbid extra fields).
3. Implement `ai/providers.py` abstraction:
   - `EmergentProvider` (zero-config default via `EMERGENT_LLM_KEY`)
   - BYOK providers: OpenAI, Anthropic, Gemini (keys stored later; for POC read from env).
4. Implement robust prompt + parsing:
   - Use “return JSON only” instruction, include schema in prompt, add self-check (“if uncertain, set confidence low”).
   - Add validator + retry-on-parse-fail (max 2 retries).
5. Create **`test_core.py`** (single script) that:
   - Calls Emergent default model to classify 6–10 sample brain dumps (idea/task/project/problem/goal/note).
   - Asserts JSON parses, required fields exist, enums valid, and confidence in [0,1].
   - Calls weekly review generator on seeded sample dataset; asserts keys present and summaries non-empty.
6. Run until green; iterate prompts/providers until stable.

**Exit criteria**
- `python test_core.py` passes consistently (structured JSON, validated, minimal hallucinated fields).

---

### Phase 2 — V1 App Development (No auth initially)
**User stories (V1 core UX)**
1. As a user, I can quick-capture text or voice from anywhere and it lands in Inbox as “unprocessed”.
2. As a user, I can open an Inbox item and apply AI suggestions to convert it into a Task, Project, or Incubated Idea.
3. As a user, I can see “Next Actions” only, filtered by time/energy and task type, so I always know what to do now.
4. As a user, I can view Projects with a clear Priority Score visualization and a single next action.
5. As a user, I can run a Weekly Review and get actionable recommendations (freeze/delegate/resolve conflicts).

**Backend (FastAPI + MongoDB/motor)**
1. Create DB models/collections for: users (stub), areas, inbox_items, projects, tasks, ideas, reviews, notes, links.
2. Implement CRUD routes under `/api` for all entities (minimal fields first; match provided schema).
3. Implement AI routes:
   - `POST /api/ai/classify-inbox` (accepts text, optional provider selection)
   - `POST /api/ai/generate-review` (uses week_ref + DB data)
4. Implement conversion endpoints:
   - `POST /api/inbox/{id}/convert` → creates task/project/idea + links + archives inbox item.
   - `POST /api/ideas/{id}/promote` → idea → project.
5. Implement priority scoring util + store component scores; compute `priority_score` server-side.
6. Seed endpoint `POST /api/dev/seed` to insert demo data (areas + 10 inbox + 3–5 projects + 8 tasks + 5 ideas + 1 review).

**Frontend (React + Tailwind + shadcn/ui + Framer Motion + Lucide)**
1. App shell: premium sidebar + minimal header (search, quick add, profile placeholder), dark mode default.
2. i18n (IT/EN) with language toggle; strings for nav/pages/core actions.
3. Pages (8): Dashboard, Inbox, Projects, Tasks/Next Actions, Areas, Incubator, Reviews, Settings.
4. Core UI components:
   - Bento dashboard cards (unprocessed inbox, today actions, top weekly priorities, projects, incubator, areas summary).
   - Quick Capture modal (text + voice transcription via Web Speech API).
   - Inbox processing drawer: AI suggestion panel + “Convert to …” actions.
   - Priority badge/score bar; task chips (type/energy/time).
   - Relations mini-panel (idea↔project links).
5. Data flow: React Query (or equivalent) for API calls; loading/empty/error states everywhere.
6. Settings page:
   - Provider select (Emergent default / OpenAI / Anthropic / Gemini)
   - BYOK key inputs (stored later; for V1 can store in backend DB without auth, scoped to a demo user).

**Testing (end of Phase 2)**
- Run one full E2E pass with testing agent: seed → dashboard renders → capture (text+voice) → AI classify → convert → next actions filters → review generation.

---

### Phase 3 — Auth + Provider Settings Hardening
**User stories (auth & security)**
1. As a user, I can sign up/login with email/password and my data is private.
2. As a user, I can sign in with Google and return without losing my workspace.
3. As a user, I can store my AI provider keys securely and switch provider per request.
4. As a user, I can delete my stored provider keys at any time.
5. As a user, I can log out and ensure the app clears sensitive state.

**Steps**
1. Email/password auth: bcrypt hashing + JWT; protect all CRUD routes.
2. Google OAuth: Emergent-managed flow; map/create user; issue JWT/session.
3. Migrate Settings storage to per-user encrypted-at-rest (MVP: server-side env-like storage; best-effort encryption).
4. Add role/dev guard for seed endpoint.
5. Retest E2E with auth on (testing agent).

---

### Phase 4 — Polish (Premium feel) + Reliability
**User stories (polish)**
1. As a user, I can process Inbox quickly with keyboard shortcuts and smooth microinteractions.
2. As a user, I can see “stuck projects” and “overload warnings” surfaced on Dashboard.
3. As a user, I can search across inbox/projects/tasks/ideas instantly.
4. As a user, I can link items with minimal friction (relations graph-lite).
5. As a user, I can export my data (JSON/CSV) as a safety net.

**Steps**
- UX refinements: animations, hover states, skeletons, empty states, responsive tuning.
- AI reliability: caching, rate-limit handling, graceful fallbacks, better prompts.
- Add search endpoint + UI.
- Final regression E2E with testing agent.

## STATUS LOG
- [DONE] Phase 1 POC: `test_core.py` passed 9/9 (AI classification + weekly review, structured JSON via Emergent LLM key).
- [DONE] Phase 2 MVP: Full backend (all entities CRUD, AI classify/convert/review, priority scoring, seed, search) + full frontend (8 pages, dark glassmorphism bento UI, quick capture text+voice via Web Speech API, i18n IT/EN, provider settings BYOK+Emergent). Backend tests 45/45 (100%), Frontend tests 21/21 (100%). Single demo user (no auth yet).
- [PENDING] Phase 3: Auth (email/password + Google OAuth via Emergent) + per-user data scoping + secure key storage.
- [PENDING] Phase 4: Premium polish, overload insights, export.

## 3) Next Actions
1. Phase 3: fetch Emergent Google Auth playbook; add email/password (JWT+bcrypt) + Google login; migrate DEMO_USER_ID scoping to authenticated user; keep a testing bypass.
2. Phase 4: polish + data export + more AI insights.
NOTE: Voice capture uses browser Web Speech API (Chrome/Edge) — user must test with a real microphone.

## 4) Success Criteria
- POC: `test_core.py` passes and returns valid structured JSON for classification + weekly review.
- V1: user can seed demo data, capture text/voice, AI-classify, convert to project/task/idea, and execute next actions with filters.
- Settings: provider selection works; Emergent default works out-of-box; BYOK keys stored and used.
- UI: premium dark bento layout, clear hierarchy, smooth interactions, not cluttered.
- Testing: at least 1 full E2E run per phase without blocking bugs.