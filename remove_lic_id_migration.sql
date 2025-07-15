-- Migration to remove lic_id column and use id instead
-- Run this in Supabase SQL Editor after executing the previous schema files

-- Step 1: Drop dependent views first
DROP VIEW IF EXISTS licenses_needing_reminders;
DROP VIEW IF EXISTS upcoming_expirations;
DROP VIEW IF EXISTS overdue_licenses;

-- Step 2: Drop indexes that reference lic_id
DROP INDEX IF EXISTS idx_licenses_lic_id;

-- Step 3: Drop the lic_id column from licenses table
ALTER TABLE licenses 
DROP COLUMN IF EXISTS lic_id;

-- Step 4: Recreate the upcoming_expirations view using id instead of lic_id
CREATE VIEW upcoming_expirations AS
SELECT 
    l.*,
    l.expiration_date - CURRENT_DATE as days_until_expiration,
    CASE 
        WHEN l.expiration_date < CURRENT_DATE THEN 'overdue'
        WHEN l.expiration_date - CURRENT_DATE <= 10 THEN 'critical'
        WHEN l.expiration_date - CURRENT_DATE <= 30 THEN 'warning'
        WHEN l.expiration_date - CURRENT_DATE <= 60 THEN 'upcoming'
        ELSE 'normal'
    END as status_category
FROM licenses l
WHERE l.expiration_date IS NOT NULL 
    AND (
        l.expiration_date >= CURRENT_DATE - INTERVAL '30 days'  -- Include 30 days overdue
        AND l.expiration_date <= CURRENT_DATE + INTERVAL '90 days'  -- Include 90 days future
    )
ORDER BY l.expiration_date ASC;

-- Step 5: Recreate the licenses_needing_reminders view using id instead of lic_id
CREATE VIEW licenses_needing_reminders AS
WITH reminder_status AS (
    SELECT 
        l.id,
        l.lic_name,
        l.lic_type,
        l.lic_state,
        l.expiration_date,
        l.lic_notify_names,
        l.expiration_date - CURRENT_DATE as days_until_expiration,
        CASE 
            WHEN l.expiration_date - CURRENT_DATE = 60 THEN '60_days'
            WHEN l.expiration_date - CURRENT_DATE = 30 THEN '30_days'
            WHEN l.expiration_date - CURRENT_DATE = 15 THEN '15_days'
            WHEN l.expiration_date - CURRENT_DATE = 7 THEN '7_days'
            WHEN l.expiration_date - CURRENT_DATE = 1 THEN '1_day'
            WHEN l.expiration_date < CURRENT_DATE THEN 'overdue_daily'
            ELSE NULL
        END as reminder_type
    FROM licenses l
    WHERE l.expiration_date IS NOT NULL 
        AND l.lic_notify_names IS NOT NULL
        AND l.lic_notify_names != ''
        AND (
            -- Future reminders (60, 30, 15, 7, 1 day before)
            l.expiration_date - CURRENT_DATE IN (60, 30, 15, 7, 1)
            OR 
            -- Daily reminders for overdue licenses
            l.expiration_date < CURRENT_DATE
        )
),
recent_reminders AS (
    SELECT 
        er.license_id,
        er.reminder_type,
        MAX(er.sent_date) as last_sent_date
    FROM email_reminders er
    WHERE DATE(er.sent_date) >= CURRENT_DATE - INTERVAL '7 days'  -- Check last 7 days
    GROUP BY er.license_id, er.reminder_type
)
SELECT rs.*
FROM reminder_status rs
LEFT JOIN recent_reminders rr ON rs.id = rr.license_id 
    AND rs.reminder_type = rr.reminder_type
    AND (
        -- For specific day reminders, check if sent today
        (rs.reminder_type IN ('60_days', '30_days', '15_days', '7_days', '1_day') 
         AND DATE(rr.last_sent_date) = CURRENT_DATE)
        OR
        -- For overdue daily reminders, check if sent today
        (rs.reminder_type = 'overdue_daily' 
         AND DATE(rr.last_sent_date) = CURRENT_DATE)
    )
WHERE rr.license_id IS NULL  -- Only get licenses that haven't had reminders sent today
ORDER BY rs.days_until_expiration ASC, rs.lic_name ASC;

-- Step 6: Recreate the overdue_licenses view using id instead of lic_id
CREATE OR REPLACE VIEW overdue_licenses AS
SELECT 
    l.*,
    CURRENT_DATE - l.expiration_date as days_overdue
FROM licenses l
WHERE l.expiration_date IS NOT NULL 
    AND l.expiration_date < CURRENT_DATE
ORDER BY l.expiration_date ASC;

-- Step 7: Update the reminder statistics function to use id instead of lic_id
CREATE OR REPLACE FUNCTION get_reminder_stats()
RETURNS TABLE(
    reminder_type TEXT,
    license_count BIGINT,
    description TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE 
            WHEN l.expiration_date - CURRENT_DATE = 60 THEN '60_days'
            WHEN l.expiration_date - CURRENT_DATE = 30 THEN '30_days'
            WHEN l.expiration_date - CURRENT_DATE = 15 THEN '15_days'
            WHEN l.expiration_date - CURRENT_DATE = 7 THEN '7_days'
            WHEN l.expiration_date - CURRENT_DATE = 1 THEN '1_day'
            WHEN l.expiration_date < CURRENT_DATE THEN 'overdue_daily'
            ELSE 'other'
        END as reminder_type,
        COUNT(*) as license_count,
        CASE 
            WHEN l.expiration_date - CURRENT_DATE = 60 THEN '60 days before expiration'
            WHEN l.expiration_date - CURRENT_DATE = 30 THEN '30 days before expiration'
            WHEN l.expiration_date - CURRENT_DATE = 15 THEN '15 days before expiration'
            WHEN l.expiration_date - CURRENT_DATE = 7 THEN '7 days before expiration'
            WHEN l.expiration_date - CURRENT_DATE = 1 THEN '1 day before expiration'
            WHEN l.expiration_date < CURRENT_DATE THEN 'Overdue (daily reminders)'
            ELSE 'Other'
        END as description
    FROM licenses l
    WHERE l.expiration_date IS NOT NULL 
        AND l.lic_notify_names IS NOT NULL
        AND l.lic_notify_names != ''
    GROUP BY 
        CASE 
            WHEN l.expiration_date - CURRENT_DATE = 60 THEN '60_days'
            WHEN l.expiration_date - CURRENT_DATE = 30 THEN '30_days'
            WHEN l.expiration_date - CURRENT_DATE = 15 THEN '15_days'
            WHEN l.expiration_date - CURRENT_DATE = 7 THEN '7_days'
            WHEN l.expiration_date - CURRENT_DATE = 1 THEN '1_day'
            WHEN l.expiration_date < CURRENT_DATE THEN 'overdue_daily'
            ELSE 'other'
        END,
        CASE 
            WHEN l.expiration_date - CURRENT_DATE = 60 THEN '60 days before expiration'
            WHEN l.expiration_date - CURRENT_DATE = 30 THEN '30 days before expiration'
            WHEN l.expiration_date - CURRENT_DATE = 15 THEN '15 days before expiration'
            WHEN l.expiration_date - CURRENT_DATE = 7 THEN '7 days before expiration'
            WHEN l.expiration_date - CURRENT_DATE = 1 THEN '1 day before expiration'
            WHEN l.expiration_date < CURRENT_DATE THEN 'Overdue (daily reminders)'
            ELSE 'Other'
        END
    ORDER BY 
        CASE 
            WHEN l.expiration_date - CURRENT_DATE = 60 THEN 1
            WHEN l.expiration_date - CURRENT_DATE = 30 THEN 2
            WHEN l.expiration_date - CURRENT_DATE = 15 THEN 3
            WHEN l.expiration_date - CURRENT_DATE = 7 THEN 4
            WHEN l.expiration_date - CURRENT_DATE = 1 THEN 5
            WHEN l.expiration_date < CURRENT_DATE THEN 6
            ELSE 7
        END;
END;
$$ LANGUAGE plpgsql;

-- Verify the changes
-- SELECT * FROM licenses LIMIT 5;
-- SELECT * FROM upcoming_expirations LIMIT 5;
-- SELECT * FROM licenses_needing_reminders LIMIT 5; 