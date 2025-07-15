-- Fix RLS policies to allow anonymous access for web dashboard
-- Run this in Supabase SQL Editor

-- Drop existing restrictive policies
DROP POLICY IF EXISTS "Enable read access for authenticated users" ON licenses;
DROP POLICY IF EXISTS "Enable all access for authenticated users" ON licenses;

-- Create new policies that allow anonymous access for reading
CREATE POLICY "Enable read access for all users" ON licenses
    FOR SELECT USING (true);

CREATE POLICY "Enable insert access for all users" ON licenses
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Enable update access for all users" ON licenses
    FOR UPDATE USING (true);

-- Also fix email_reminders table
DROP POLICY IF EXISTS "Enable read access for authenticated users" ON email_reminders;
DROP POLICY IF EXISTS "Enable all access for authenticated users" ON email_reminders;

CREATE POLICY "Enable read access for all users" ON email_reminders
    FOR SELECT USING (true);

CREATE POLICY "Enable insert access for all users" ON email_reminders
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Enable update access for all users" ON email_reminders
    FOR UPDATE USING (true);

-- Note: This allows anonymous access. For production, you should use proper authentication.
-- Alternative: Use the service role key instead of the anon key in your .env file 