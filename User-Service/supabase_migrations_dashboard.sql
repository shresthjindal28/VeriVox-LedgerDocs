-- ============================================================================
-- DASHBOARD TABLES MIGRATION
-- Creates tables for voice sessions and blockchain proofs persistence
-- ============================================================================

-- ============================================================================
-- VOICE SESSIONS TABLE
-- Tracks voice call sessions for dashboard display
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.voice_sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    document_id UUID NOT NULL,
    state TEXT NOT NULL DEFAULT 'initializing',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    duration_seconds INTEGER DEFAULT 0,
    question_count INTEGER DEFAULT 0,
    transcript_status TEXT DEFAULT 'pending',
    verification_status TEXT DEFAULT 'pending',
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Enable Row Level Security
ALTER TABLE public.voice_sessions ENABLE ROW LEVEL SECURITY;

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_voice_sessions_user_id 
    ON public.voice_sessions(user_id);

CREATE INDEX IF NOT EXISTS idx_voice_sessions_document_id 
    ON public.voice_sessions(document_id);

CREATE INDEX IF NOT EXISTS idx_voice_sessions_created_at 
    ON public.voice_sessions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_voice_sessions_state 
    ON public.voice_sessions(state);

-- RLS Policies
CREATE POLICY "Users can view own sessions"
    ON public.voice_sessions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Service role full access on voice_sessions"
    ON public.voice_sessions
    USING (auth.jwt() ->> 'role' = 'service_role');

-- Allow service role to insert/update/delete
CREATE POLICY "Service role can insert sessions"
    ON public.voice_sessions FOR INSERT
    WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role can update sessions"
    ON public.voice_sessions FOR UPDATE
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role can delete sessions"
    ON public.voice_sessions FOR DELETE
    USING (auth.jwt() ->> 'role' = 'service_role');

-- Disable RLS for service-to-service communication
-- (Protected by service key in application layer)
ALTER TABLE public.voice_sessions DISABLE ROW LEVEL SECURITY;


-- ============================================================================
-- BLOCKCHAIN PROOFS TABLE
-- Stores blockchain proofs for dashboard display and verification
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.blockchain_proofs (
    proof_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proof_type TEXT NOT NULL,
    hash_value TEXT NOT NULL,
    document_id UUID,
    session_id UUID,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    tx_hash TEXT,
    block_number INTEGER,
    verified BOOLEAN DEFAULT false,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Enable Row Level Security
ALTER TABLE public.blockchain_proofs ENABLE ROW LEVEL SECURITY;

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_blockchain_proofs_user_id 
    ON public.blockchain_proofs(user_id);

CREATE INDEX IF NOT EXISTS idx_blockchain_proofs_document_id 
    ON public.blockchain_proofs(document_id);

CREATE INDEX IF NOT EXISTS idx_blockchain_proofs_session_id 
    ON public.blockchain_proofs(session_id);

CREATE INDEX IF NOT EXISTS idx_blockchain_proofs_proof_type 
    ON public.blockchain_proofs(proof_type);

CREATE INDEX IF NOT EXISTS idx_blockchain_proofs_timestamp 
    ON public.blockchain_proofs(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_blockchain_proofs_verified 
    ON public.blockchain_proofs(verified);

-- RLS Policies
CREATE POLICY "Users can view own proofs"
    ON public.blockchain_proofs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Service role full access on blockchain_proofs"
    ON public.blockchain_proofs
    USING (auth.jwt() ->> 'role' = 'service_role');

-- Allow service role to insert/update/delete
CREATE POLICY "Service role can insert proofs"
    ON public.blockchain_proofs FOR INSERT
    WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role can update proofs"
    ON public.blockchain_proofs FOR UPDATE
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role can delete proofs"
    ON public.blockchain_proofs FOR DELETE
    USING (auth.jwt() ->> 'role' = 'service_role');

-- Disable RLS for service-to-service communication
-- (Protected by service key in application layer)
ALTER TABLE public.blockchain_proofs DISABLE ROW LEVEL SECURITY;
