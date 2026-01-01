-- Add media_bin column to chat_sessions table
-- Stores media bin snapshot for session restoration
-- Format: Array of {id, name, mediaType, gcs_path, width, height, duration, text}

ALTER TABLE chat_sessions 
ADD COLUMN IF NOT EXISTS media_bin JSONB NOT NULL DEFAULT '[]';

-- Comment for documentation
COMMENT ON COLUMN chat_sessions.media_bin IS 'Array of media bin items: {id, name, mediaType, gcs_path, width, height, duration, text}. URLs are regenerated on load.';
