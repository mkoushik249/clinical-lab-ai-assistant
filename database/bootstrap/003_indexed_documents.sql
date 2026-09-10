CREATE TABLE IF NOT EXISTS indexed_documents (
    source_name VARCHAR(255) PRIMARY KEY,
    document_hash VARCHAR(64) NOT NULL,
    last_indexed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
); 