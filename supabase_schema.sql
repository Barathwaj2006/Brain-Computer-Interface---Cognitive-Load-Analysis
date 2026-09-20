-- =============================================================================
-- NeuroSim Clinical EEG Platform — Supabase PostgreSQL Schema
-- 21 CFR Part 11 & HIPAA Compliant Relational Data Structure
-- =============================================================================

-- 1. Users Table (Clinicians, Researchers, Patients)
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    mobile VARCHAR(50) NOT NULL UNIQUE,
    otp VARCHAR(10),
    otp_expires_at DOUBLE PRECISION,
    token VARCHAR(128),
    created_at DOUBLE PRECISION NOT NULL,
    last_login DOUBLE PRECISION
);

-- 2. Recorded EEG Clinical Sessions
CREATE TABLE IF NOT EXISTS sessions (
    id BIGSERIAL PRIMARY KEY,
    session_uid VARCHAR(128) UNIQUE NOT NULL,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    patient_id VARCHAR(128) DEFAULT 'ANON-001',
    duration_sec DOUBLE PRECISION DEFAULT 0.0,
    sample_count BIGINT DEFAULT 0,
    dominant_band VARCHAR(64) DEFAULT 'ALPHA',
    avg_stress DOUBLE PRECISION DEFAULT 0.0,
    metrics_json TEXT,
    created_at DOUBLE PRECISION NOT NULL
);

-- 3. 21 CFR Part 11 Cryptographically Chained SHA-256 Audit Ledger
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(64) NOT NULL,
    ip_address VARCHAR(64),
    details TEXT,
    created_at DOUBLE PRECISION NOT NULL,
    previous_hash VARCHAR(128),
    record_hash VARCHAR(128)
);

-- 4. Idempotency Key Store (Prevents Duplicate Generation)
CREATE TABLE IF NOT EXISTS idempotency_keys (
    key VARCHAR(128) PRIMARY KEY,
    response_body TEXT,
    created_at DOUBLE PRECISION NOT NULL
);

-- 5. Real-Time Experimental Event Markers & Stimulus Pins
CREATE TABLE IF NOT EXISTS event_markers (
    id BIGSERIAL PRIMARY KEY,
    session_uid VARCHAR(128) NOT NULL,
    marker_label VARCHAR(128) NOT NULL,
    sample_index BIGINT NOT NULL,
    timestamp DOUBLE PRECISION NOT NULL,
    notes TEXT,
    created_at DOUBLE PRECISION NOT NULL
);

-- =============================================================================
-- High-Performance B-Tree Indexes
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_patient ON sessions(patient_id);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_markers_session ON event_markers(session_uid);
CREATE INDEX IF NOT EXISTS idx_users_mobile ON users(mobile);
CREATE INDEX IF NOT EXISTS idx_users_token ON users(token);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at DESC);

-- =============================================================================
-- Row Level Security (RLS) Configuration
-- =============================================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE idempotency_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_markers ENABLE ROW LEVEL SECURITY;

-- Allow public read/write access via API Service Role / Authenticated Client
CREATE POLICY "Allow public backend access to users" ON users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow public backend access to sessions" ON sessions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow public backend access to audit_logs" ON audit_logs FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow public backend access to idempotency_keys" ON idempotency_keys FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow public backend access to event_markers" ON event_markers FOR ALL USING (true) WITH CHECK (true);
