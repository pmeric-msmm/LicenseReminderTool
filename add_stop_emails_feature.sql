-- Add Stop Emails Feature
-- Run this in Supabase SQL Editor

-- Add email_enabled column to licenses table
ALTER TABLE licenses 
ADD COLUMN email_enabled BOOLEAN DEFAULT true;

-- Add comment for clarity
COMMENT ON COLUMN licenses.email_enabled IS 'Controls whether email reminders should be sent for this license';

-- Update the licenses_needing_reminders view to respect the email_enabled setting
DROP VIEW IF EXISTS licenses_needing_reminders;

CREATE VIEW licenses_needing_reminders AS
WITH reminder_status AS (
    SELECT 
        l.id,
        l.lic_name,
        l.lic_type,
        l.lic_state,
        l.expiration_date,
        l.lic_notify_names,
        l.email_enabled,
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
        AND l.email_enabled = true  -- Only include licenses with emails enabled
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

-- Create an index on the new column for better performance
CREATE INDEX idx_licenses_email_enabled ON licenses(email_enabled);

-- Optional: Check current data
-- SELECT lic_name, email_enabled, lic_notify_names FROM licenses LIMIT 10; 