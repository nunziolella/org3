-- Migration: 0002_org3_outbox.sql
-- Description: Creates the outbox table for reliable Event Sourcing to Neo4j.

CREATE TABLE IF NOT EXISTS org3_outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type VARCHAR(64) NOT NULL, -- e.g., 'member', 'delegation_policy'
    aggregate_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(64) NOT NULL,     -- e.g., 'MEMBER_CREATED', 'POLICY_REVOKED'
    payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    is_processed BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_org3_outbox_unprocessed ON org3_outbox (created_at) WHERE is_processed = FALSE;
