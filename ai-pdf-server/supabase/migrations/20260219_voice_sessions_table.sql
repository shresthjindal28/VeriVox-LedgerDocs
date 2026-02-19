-- Create voice_sessions table (stores voice call data per user)
-- Run this in Supabase SQL Editor if voice_sessions does not exist.

CREATE TABLE IF NOT EXISTS voice_sessions (
  session_id     TEXT PRIMARY KEY,
  user_id        TEXT NOT NULL,
  document_id    TEXT NOT NULL,
  state          TEXT NOT NULL DEFAULT 'initializing',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ended_at       TIMESTAMPTZ,
  duration_seconds INTEGER DEFAULT 0,
  question_count  INTEGER NOT NULL DEFAULT 0,
  first_question  TEXT,
  transcript_status TEXT NOT NULL DEFAULT 'pending',
  verification_status TEXT NOT NULL DEFAULT 'pending',
  metadata       JSONB DEFAULT '{}'
);

COMMENT ON TABLE voice_sessions IS 'Voice call sessions per user; session_id is the call id, first_question is the first user question.';
COMMENT ON COLUMN voice_sessions.first_question IS 'First question the user asked in this voice session';

-- Optional: index for listing by user
CREATE INDEX IF NOT EXISTS idx_voice_sessions_user_id ON voice_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_voice_sessions_created_at ON voice_sessions (created_at DESC);
