-- Guardian Database Initialization
-- This script runs when the PostgreSQL container is first created

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS guardian_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- Create tokens table
CREATE TABLE IF NOT EXISTS guardian_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES guardian_users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_guardian_users_email ON guardian_users(email);
CREATE INDEX IF NOT EXISTS ix_guardian_tokens_user_id ON guardian_tokens(user_id);
CREATE INDEX IF NOT EXISTS ix_guardian_tokens_token_hash ON guardian_tokens(token_hash);

-- Insert test user (optional - for development)
-- INSERT INTO guardian_users (email, is_active) VALUES ('test@guardian.local', true)
-- ON CONFLICT (email) DO NOTHING;

COMMENT ON TABLE guardian_users IS 'Guardian user accounts for authentication';
COMMENT ON TABLE guardian_tokens IS '6-digit authentication tokens for passwordless login';
