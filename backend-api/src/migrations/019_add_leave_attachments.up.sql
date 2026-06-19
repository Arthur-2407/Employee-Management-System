-- Migration 019: Add leave attachments
ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS attachment_data TEXT;
ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS attachment_name TEXT;
