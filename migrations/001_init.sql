-- migrations/001_init.sql
-- Create extensions if needed (on Supabase gen_random_uuid() uses pgcrypto or pgjwt)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- model_profiles table
CREATE TABLE IF NOT EXISTS model_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  provider TEXT NOT NULL, -- 'openai' | 'anthropic'
  base_model TEXT NOT NULL,
  system_prompt TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- chats table
CREATE TABLE IF NOT EXISTS chats (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT,
  model_profile_id UUID REFERENCES model_profiles(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- messages table
CREATE TABLE IF NOT EXISTS messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chat_id UUID REFERENCES chats(id) ON DELETE CASCADE,
  role TEXT NOT NULL, -- 'user' | 'assistant' | 'system'
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- index for fetching recent messages quickly
CREATE INDEX IF NOT EXISTS idx_messages_chat_created_at ON messages(chat_id, created_at DESC);


-- pgcrypto offers gen_random_uuid(). If your Postgres doesn't have it, you can use uuid_generate_v4().

-- model_profile_id is referenced in chats to know which profile the chat originally used. Requirement: when user edits model profile, subsequent messages use updated profile — we'll implement that by always loading the current model_profiles row by id at the time of each message dispatch.