-- Migration: Enhanced Biometric Security & Challenge Tracking
-- Date: 2026-06-20
-- Purpose: Add comprehensive anti-spoofing, liveness challenges, and deepfake detection infrastructure

-- ============================================================================
-- 1. AUTHENTICATION_CHALLENGES TABLE - Track active liveness challenges
-- ============================================================================
CREATE TABLE IF NOT EXISTS authentication_challenges (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    session_id VARCHAR(128) NOT NULL UNIQUE,
    challenge_type VARCHAR(50) NOT NULL CHECK (challenge_type IN (
        'BLINK', 'BLINK_TWICE', 'HEAD_LEFT', 'HEAD_RIGHT', 
        'LOOK_UP', 'LOOK_DOWN', 'SMILE', 'OPEN_MOUTH',
        'MULTI_CHALLENGE'
    )),
    challenge_completed BOOLEAN DEFAULT FALSE,
    confidence_score FLOAT DEFAULT 0.0,
    completion_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '5 minutes'),
    CONSTRAINT valid_expiry CHECK (expires_at > created_at)
);

CREATE INDEX IF NOT EXISTS idx_auth_challenges_employee ON authentication_challenges(employee_id);
CREATE INDEX IF NOT EXISTS idx_auth_challenges_session ON authentication_challenges(session_id);
CREATE INDEX IF NOT EXISTS idx_auth_challenges_completed ON authentication_challenges(challenge_completed);

-- ============================================================================
-- 2. LIVENESS_DETECTION_LOGS TABLE - Comprehensive liveness audit trail
-- ============================================================================
CREATE TABLE IF NOT EXISTS liveness_detection_logs (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    login_attempt_id BIGINT,  -- Links to login_logs.id
    frames_analyzed INTEGER DEFAULT 0,
    blink_detected BOOLEAN,
    blink_count INTEGER,
    head_movement_detected BOOLEAN,
    head_movement_magnitude FLOAT,
    depth_variation_detected BOOLEAN,
    depth_variation_score FLOAT,
    micro_texture_variance FLOAT,
    micro_texture_live BOOLEAN,
    flow_entropy FLOAT,
    flow_naturalness_live BOOLEAN,
    overall_liveness_confidence FLOAT,
    liveness_passed BOOLEAN DEFAULT FALSE,
    failure_reasons TEXT[],  -- Array of reasons for failure
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_liveness_employee ON liveness_detection_logs(employee_id);
CREATE INDEX IF NOT EXISTS idx_liveness_passed ON liveness_detection_logs(liveness_passed);
CREATE INDEX IF NOT EXISTS idx_liveness_timestamp ON liveness_detection_logs(created_at);

-- ============================================================================
-- 3. SPOOF_DETECTION_ANALYSIS TABLE - Detailed anti-spoofing metrics
-- ============================================================================
CREATE TABLE IF NOT EXISTS spoof_detection_analysis (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    login_attempt_id BIGINT,
    frames_analyzed INTEGER DEFAULT 0,
    texture_analysis_score FLOAT,
    texture_analysis_triggered BOOLEAN,
    moire_patterns_score FLOAT,
    moire_patterns_triggered BOOLEAN,
    screen_glare_score FLOAT,
    screen_glare_triggered BOOLEAN,
    color_consistency_score FLOAT,
    color_consistency_triggered BOOLEAN,
    pixel_patterns_score FLOAT,
    pixel_patterns_triggered BOOLEAN,
    temporal_consistency_score FLOAT,
    temporal_consistency_triggered BOOLEAN,
    overall_spoof_confidence FLOAT,
    spoof_detected BOOLEAN DEFAULT FALSE,
    primary_detection_type VARCHAR(100),
    triggered_methods TEXT[],  -- Array of which methods fired
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_spoof_employee ON spoof_detection_analysis(employee_id);
CREATE INDEX IF NOT EXISTS idx_spoof_detected ON spoof_detection_analysis(spoof_detected);
CREATE INDEX IF NOT EXISTS idx_spoof_timestamp ON spoof_detection_analysis(created_at);

-- ============================================================================
-- 4. DEEPFAKE_DETECTION_LOGS TABLE - Deepfake-specific metrics
-- ============================================================================
CREATE TABLE IF NOT EXISTS deepfake_detection_logs (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    login_attempt_id BIGINT,
    frames_analyzed INTEGER DEFAULT 0,
    landmark_stability_score FLOAT,
    landmark_stable BOOLEAN,
    lip_sync_score FLOAT,
    lip_sync_anomaly_detected BOOLEAN,
    eye_mouth_correlation_score FLOAT,
    eye_mouth_correlated BOOLEAN,
    temporal_consistency_score FLOAT,
    temporal_anomaly_detected BOOLEAN,
    face_mesh_variance FLOAT,
    mesh_variance_anomaly BOOLEAN,
    overall_deepfake_confidence FLOAT,
    deepfake_suspected BOOLEAN DEFAULT FALSE,
    anomalies_detected TEXT[],  -- Array of detected anomalies
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_deepfake_employee ON deepfake_detection_logs(employee_id);
CREATE INDEX IF NOT EXISTS idx_deepfake_suspected ON deepfake_detection_logs(deepfake_suspected);
CREATE INDEX IF NOT EXISTS idx_deepfake_timestamp ON deepfake_detection_logs(created_at);

-- ============================================================================
-- 5. AUTHENTICATION_RISK_SCORES TABLE - Unified security scoring
-- ============================================================================
CREATE TABLE IF NOT EXISTS authentication_risk_scores (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    login_attempt_id BIGINT,
    face_match_score FLOAT,
    liveness_score FLOAT,
    depth_score FLOAT,
    texture_score FLOAT,
    head_pose_score FLOAT,
    blink_score FLOAT,
    frame_consistency_score FLOAT,
    mesh_score FLOAT,
    deepfake_score FLOAT,
    unified_risk_score FLOAT,
    risk_level VARCHAR(20) CHECK (risk_level IN ('ACCEPT', 'REVIEW', 'REJECT')),
    decision_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_risk_scores_employee ON authentication_risk_scores(employee_id);
CREATE INDEX IF NOT EXISTS idx_risk_scores_level ON authentication_risk_scores(risk_level);
CREATE INDEX IF NOT EXISTS idx_risk_scores_timestamp ON authentication_risk_scores(created_at);

-- ============================================================================
-- 6. ADD AUDIT COLUMNS TO EXISTING LOGIN_LOGS TABLE
-- ============================================================================
ALTER TABLE login_logs 
ADD COLUMN IF NOT EXISTS liveness_confidence FLOAT,
ADD COLUMN IF NOT EXISTS deepfake_score FLOAT,
ADD COLUMN IF NOT EXISTS challenge_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS challenge_completed BOOLEAN,
ADD COLUMN IF NOT EXISTS all_frames_passed BOOLEAN,
ADD COLUMN IF NOT EXISTS frame_count INTEGER,
ADD COLUMN IF NOT EXISTS risk_score FLOAT,
ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20),
ADD COLUMN IF NOT EXISTS audit_metadata JSONB DEFAULT '{}'::jsonb;

-- Create additional indexes for audit queries
CREATE INDEX IF NOT EXISTS idx_login_logs_liveness ON login_logs(liveness_confidence);
CREATE INDEX IF NOT EXISTS idx_login_logs_deepfake ON login_logs(deepfake_score);
CREATE INDEX IF NOT EXISTS idx_login_logs_challenge ON login_logs(challenge_type);
CREATE INDEX IF NOT EXISTS idx_login_logs_risk_level ON login_logs(risk_level);

-- ============================================================================
-- 7. GRANT PERMISSIONS (PostgreSQL)
-- ============================================================================
-- Ensure tables are owned by postgres user (adjust as needed for your setup)
ALTER TABLE authentication_challenges OWNER TO postgres;
ALTER TABLE liveness_detection_logs OWNER TO postgres;
ALTER TABLE spoof_detection_analysis OWNER TO postgres;
ALTER TABLE deepfake_detection_logs OWNER TO postgres;
ALTER TABLE authentication_risk_scores OWNER TO postgres;

-- ============================================================================
-- Cleanup: Remove old expired challenge sessions (run periodically via cron)
-- ============================================================================
-- DELETE FROM authentication_challenges WHERE expires_at < NOW();
