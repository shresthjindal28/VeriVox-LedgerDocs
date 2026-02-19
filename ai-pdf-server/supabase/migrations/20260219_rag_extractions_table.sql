-- RAG extractions: one row per exhaustive extraction run (e.g. "list all projects")
-- Used for dashboard "Total Extractions" count and "Recent Extractions" list.

CREATE TABLE IF NOT EXISTS rag_extractions (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           TEXT NOT NULL,
  document_id       TEXT NOT NULL,
  query             TEXT NOT NULL,
  item_count        INTEGER NOT NULL DEFAULT 0,
  pages_scanned     INTEGER NOT NULL DEFAULT 0,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rag_extractions_user_id ON rag_extractions (user_id);
CREATE INDEX IF NOT EXISTS idx_rag_extractions_created_at ON rag_extractions (created_at DESC);

COMMENT ON TABLE rag_extractions IS 'RAG exhaustive extraction runs per user; powers Total Extractions and Recent Extractions on dashboard';
