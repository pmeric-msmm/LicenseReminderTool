-- Fix for upcoming_expirations view
-- The current view includes expired licenses which breaks the Critical Licenses display
-- Run this in Supabase SQL Editor

-- Drop and recreate the upcoming_expirations view to only include future expirations
DROP VIEW IF EXISTS upcoming_expirations;

CREATE VIEW upcoming_expirations AS
SELECT 
    l.*,
    l.expiration_date - CURRENT_DATE as days_until_expiration,
    CASE 
        WHEN l.expiration_date - CURRENT_DATE <= 10 THEN 'critical'
        WHEN l.expiration_date - CURRENT_DATE <= 30 THEN 'warning'
        WHEN l.expiration_date - CURRENT_DATE <= 60 THEN 'upcoming'
        ELSE 'normal'
    END as status_category
FROM licenses l
WHERE l.expiration_date IS NOT NULL 
    AND l.expiration_date >= CURRENT_DATE  -- Only future expirations
    AND l.expiration_date <= CURRENT_DATE + INTERVAL '90 days'  -- Include up to 90 days future
ORDER BY l.expiration_date ASC; 