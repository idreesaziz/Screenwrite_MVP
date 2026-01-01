-- Chat Sessions Table
-- Stores minimal session metadata, messages, and composition state
-- Media files are stored in GCS at user_id/session_id/...

CREATE TABLE IF NOT EXISTS chat_sessions (
  id UUID PRIMARY KEY,  -- This IS the session_id (matches GCS prefix)
  user_id UUID NOT NULL,
  title TEXT NOT NULL DEFAULT 'New Chat',
  messages JSONB NOT NULL DEFAULT '[]',  -- Array of {role, content, timestamp}
  composition JSONB NOT NULL DEFAULT '[]',  -- The blueprint JSON
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for fast user lookups sorted by recency
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id 
  ON chat_sessions(user_id, updated_at DESC);

-- Enable Row Level Security
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only access their own sessions
CREATE POLICY "Users can only access their own sessions" 
  ON chat_sessions 
  FOR ALL 
  USING (auth.uid() = user_id);

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at on row update
DROP TRIGGER IF EXISTS update_chat_sessions_updated_at ON chat_sessions;
CREATE TRIGGER update_chat_sessions_updated_at
  BEFORE UPDATE ON chat_sessions
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
