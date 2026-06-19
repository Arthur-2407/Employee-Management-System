-- Rollback Migration 019: Remove leave attachments
ALTER TABLE leave_requests DROP COLUMN IF EXISTS attachment_data;
ALTER TABLE leave_requests DROP COLUMN IF EXISTS attachment_name;
