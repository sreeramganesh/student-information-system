-- ============================================================
-- Safe Attendance Status Migration & Constraint Verification
-- Database: sis_db
-- ============================================================
-- This migration script documents the canonical attendance statuses
-- and provides safe DDL commands to inspect or expand status constraints
-- without deleting or resetting existing records.
-- ============================================================

USE sis_db;

-- 1. Verify existing records all adhere to valid statuses
SELECT status, COUNT(*) AS record_count 
FROM attendance 
GROUP BY status;

-- 2. Current standard constraint enforces ('present', 'absent')
-- If your institution currently enforces binary attendance:
-- (No schema changes are necessary as chk_att_status is already applied).

-- 3. OPTIONAL EXTENSION: If your institution elects to support 'on_leave':
-- Run the following commands to safely upgrade the constraint:
/*
ALTER TABLE attendance DROP CHECK chk_att_status;

ALTER TABLE attendance 
  ADD CONSTRAINT chk_att_status CHECK (status IN ('present', 'absent', 'on_leave'));
*/

-- 4. Rollback commands to return to strict ('present', 'absent'):
/*
-- Ensure no active 'on_leave' rows exist prior to rollback:
UPDATE attendance SET status = 'absent' WHERE status = 'on_leave';

ALTER TABLE attendance DROP CHECK chk_att_status;

ALTER TABLE attendance 
  ADD CONSTRAINT chk_att_status CHECK (status IN ('present', 'absent'));
*/
