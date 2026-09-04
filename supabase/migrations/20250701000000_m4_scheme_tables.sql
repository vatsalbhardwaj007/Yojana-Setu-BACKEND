-- Phase 1 M4: Scheme Data Infrastructure
-- Creates exactly six tables for scheme metadata, eligibility rules, documents,
-- tutorials, verification, and profile fields.

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- 1. schemes (parent table)
-- ============================================================
CREATE TABLE schemes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_code     TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    description     TEXT NOT NULL,
    ministry        TEXT NOT NULL,
    department      TEXT NOT NULL,
    scheme_type     TEXT NOT NULL CHECK (scheme_type IN (
                        'subsidy', 'insurance', 'pension', 'benefit',
                        'loan_guarantee', 'scholarship', 'employment',
                        'healthcare', 'housing', 'other'
                    )),
    status          TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    aliases         JSONB DEFAULT '[]'::jsonb,
    target_groups   JSONB DEFAULT '[]'::jsonb,
    tags            JSONB DEFAULT '[]'::jsonb,
    benefits        JSONB DEFAULT '[]'::jsonb,
    official_url    TEXT,
    effective_from  DATE NOT NULL,
    effective_to    DATE,
    last_verified_at TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE schemes IS 'Top-level government scheme metadata. scheme_code is the stable canonical identifier.';

CREATE INDEX idx_schemes_scheme_type ON schemes (scheme_type);
CREATE INDEX idx_schemes_status ON schemes (status);
CREATE INDEX idx_schemes_ministry ON schemes (ministry);

-- ============================================================
-- 2. scheme_rules (eligibility rules — AND-only, no OR)
-- ============================================================
CREATE TABLE scheme_rules (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_id   UUID NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    rule_group  TEXT NOT NULL,
    field       TEXT NOT NULL,
    operator    TEXT NOT NULL CHECK (operator IN (
                    '=', '!=', '>=', '<=', '>', '<',
                    'in', 'not_in', 'exists', 'between'
                )),
    value       JSONB NOT NULL,
    description TEXT NOT NULL,
    rule_purpose    TEXT NOT NULL DEFAULT 'eligibility' CHECK (rule_purpose IN ('eligibility', 'exclusion')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE scheme_rules IS 'Eligibility rules per scheme. MVP: AND-only logic. No OR, no nesting.';

CREATE INDEX idx_scheme_rules_scheme_id ON scheme_rules (scheme_id);
CREATE INDEX idx_scheme_rules_rule_group ON scheme_rules (rule_group);
CREATE INDEX idx_scheme_rules_field ON scheme_rules (field);

-- ============================================================
-- 3. scheme_documents (required/recommended documents)
-- ============================================================
CREATE TABLE scheme_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_id       UUID NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    document_type   TEXT NOT NULL CHECK (document_type IN (
                        'identity_proof', 'address_proof', 'income_proof',
                        'category_certificate', 'age_proof', 'land_record',
                        'bank_details', 'photograph', 'declaration', 'other'
                    )),
    document_name   TEXT NOT NULL,
    is_mandatory    BOOLEAN NOT NULL DEFAULT true,
    description     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE scheme_documents IS 'Documents required or recommended for a scheme application.';

CREATE INDEX idx_scheme_documents_scheme_id ON scheme_documents (scheme_id);
CREATE INDEX idx_scheme_documents_document_type ON scheme_documents (document_type);

-- ============================================================
-- 4. tutorial_steps (step-by-step application guidance)
-- ============================================================
CREATE TABLE tutorial_steps (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_id   UUID NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL CHECK (step_number >= 1),
    title       TEXT NOT NULL,
    description TEXT NOT NULL,
    tips        TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (scheme_id, step_number)
);

COMMENT ON TABLE tutorial_steps IS 'Sequential application guidance steps per scheme.';

CREATE INDEX idx_tutorial_steps_scheme_id ON tutorial_steps (scheme_id);

-- ============================================================
-- 5. scheme_verification (verification & contact details)
-- ============================================================
CREATE TABLE scheme_verification (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_id           UUID NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    verification_method TEXT NOT NULL CHECK (verification_method IN ('online', 'offline', 'both')),
    verification_url    TEXT,
    helpline_number     TEXT,
    last_verified_at    TIMESTAMPTZ NOT NULL,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE scheme_verification IS 'Verification methods, URLs, and helpline contact for each scheme.';

CREATE INDEX idx_scheme_verification_scheme_id ON scheme_verification (scheme_id);

-- ============================================================
-- 6. scheme_profile_fields (user data requirements per scheme)
-- ============================================================
CREATE TABLE scheme_profile_fields (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_id       UUID NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    field_name      TEXT NOT NULL,
    field_type      TEXT NOT NULL CHECK (field_type IN ('text', 'number', 'date', 'boolean', 'select')),
    is_required     BOOLEAN NOT NULL DEFAULT true,
    allowed_values  JSONB,
    description     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (scheme_id, field_name)
);

COMMENT ON TABLE scheme_profile_fields IS 'User profile fields required by each scheme for eligibility checks.';

CREATE INDEX idx_scheme_profile_fields_scheme_id ON scheme_profile_fields (scheme_id);

-- ============================================================
-- updated_at trigger
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_schemes_updated_at
    BEFORE UPDATE ON schemes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
