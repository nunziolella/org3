-- ============================================================================
-- ORG3 PLATFORM — MULTI-TENANT & GOVERNANCE SCHEMA
-- Versione: 1.0.0 (DEC-04/10)
-- Target: Neon PostgreSQL (Cluster ep-wandering-rain-ad3ciuur)
-- Namespace: org3_* (Strict Non-Contamination Invariant)
-- ============================================================================

-- Abilita l'estensione pgcrypto se non presente (per gen_random_uuid)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1. Organizzazioni (Tenants)
CREATE TABLE IF NOT EXISTS org3_organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    plan VARCHAR(32) NOT NULL DEFAULT 'free', -- free, business, enterprise
    owner_email VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_org3_organizations_slug ON org3_organizations(slug);
CREATE INDEX IF NOT EXISTS idx_org3_organizations_owner ON org3_organizations(owner_email);

-- 2. Workspace & Cloud Storage Connections
CREATE TABLE IF NOT EXISTS org3_workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES org3_organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    storage_provider VARCHAR(32) NOT NULL DEFAULT 'google_drive', -- google_drive, s3, r2, local_fs
    storage_config JSONB NOT NULL DEFAULT '{}'::jsonb, -- root_folder_id, bucket_name, credentials_ref
    is_primary BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_org3_workspaces_org ON org3_workspaces(org_id);

-- 3. Membri (Umani, Agenti AI, Worker)
CREATE TABLE IF NOT EXISTS org3_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES org3_organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    member_type VARCHAR(32) NOT NULL DEFAULT 'HUMAN', -- HUMAN, AI_SYSTEM, WORKER_SERVICE
    role VARCHAR(64) NOT NULL DEFAULT 'OPERATOR',     -- FOUNDER_GODMODE, CEO, VP, TECH_LEAD, OPERATOR, VIEWER
    is_master BOOLEAN NOT NULL DEFAULT false,        -- God Mode per Nunzio Lella
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_org3_members_org_email UNIQUE(org_id, email)
);

CREATE INDEX IF NOT EXISTS idx_org3_members_org_role ON org3_members(org_id, role);
CREATE INDEX IF NOT EXISTS idx_org3_members_email ON org3_members(email);

-- 4. Contratti di Delega Condizionata (Delegation Policies)
CREATE TABLE IF NOT EXISTS org3_delegation_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES org3_organizations(id) ON DELETE CASCADE,
    actor_id UUID NOT NULL REFERENCES org3_members(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    scope VARCHAR(128) NOT NULL, -- quotes, roadmap, deployments, purchasing, intellectual_property
    max_financial_authority NUMERIC(12, 2) DEFAULT 0.00,
    constraints JSONB NOT NULL DEFAULT '[]'::jsonb, -- ["NO_IP_CONCESSION", "NO_EXCLUSIVITY", "NO_ROADMAP_COMMITMENT"]
    approval_gate VARCHAR(32) NOT NULL DEFAULT 'CLASS_C', -- CLASS_A (auto), CLASS_B (evidence), CLASS_C (human), CLASS_D (master)
    is_revoked BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_org3_delegation_org_actor ON org3_delegation_policies(org_id, actor_id);
CREATE INDEX IF NOT EXISTS idx_org3_delegation_scope ON org3_delegation_policies(scope);

-- 5. Hub Notifiche & Approvazioni Human-in-the-Loop (HITL)
CREATE TABLE IF NOT EXISTS org3_approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES org3_organizations(id) ON DELETE CASCADE,
    source_service VARCHAR(64) NOT NULL DEFAULT 'structura', -- structura, memograph, external_mcp
    risk_class VARCHAR(8) NOT NULL DEFAULT 'C', -- A, B, C, D
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    requested_by UUID REFERENCES org3_members(id) ON DELETE SET NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING', -- PENDING, APPROVED, REJECTED, EXPIRED
    resolution_note TEXT,
    resolved_by UUID REFERENCES org3_members(id) ON DELETE SET NULL,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_org3_approval_org_status ON org3_approval_requests(org_id, status);
CREATE INDEX IF NOT EXISTS idx_org3_approval_risk ON org3_approval_requests(risk_class);

-- 6. Token API & Org3 Connect
CREATE TABLE IF NOT EXISTS org3_api_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES org3_organizations(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES org3_members(id) ON DELETE CASCADE,
    token_hash VARCHAR(128) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    allowed_scopes JSONB NOT NULL DEFAULT '["read", "write"]'::jsonb,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_org3_api_tokens_hash ON org3_api_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_org3_api_tokens_member ON org3_api_tokens(member_id);
