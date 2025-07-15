-- License Management System Database Schema for Supabase

-- Create licenses table
CREATE TABLE licenses (
    id SERIAL PRIMARY KEY,
    lic_id INTEGER UNIQUE NOT NULL,
    lic_name TEXT NOT NULL,
    lic_state TEXT,
    lic_type TEXT,
    lic_no TEXT,
    ascem_no BIGINT,
    first_issue_date DATE,
    expiration_date DATE,
    lic_notify_names TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create email_reminders table to track sent reminders
CREATE TABLE email_reminders (
    id SERIAL PRIMARY KEY,
    license_id INTEGER REFERENCES licenses(id) ON DELETE CASCADE,
    reminder_type TEXT NOT NULL CHECK (reminder_type IN ('30_days', '15_days', '10_days')),
    sent_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    email_addresses TEXT NOT NULL,
    email_subject TEXT,
    email_body TEXT,
    status TEXT DEFAULT 'sent' CHECK (status IN ('sent', 'failed', 'pending')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_licenses_expiration_date ON licenses(expiration_date);
CREATE INDEX idx_licenses_lic_id ON licenses(lic_id);
CREATE INDEX idx_licenses_lic_name ON licenses(lic_name);
CREATE INDEX idx_email_reminders_license_id ON email_reminders(license_id);
CREATE INDEX idx_email_reminders_reminder_type ON email_reminders(reminder_type);
CREATE INDEX idx_email_reminders_sent_date ON email_reminders(sent_date);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_licenses_updated_at 
    BEFORE UPDATE ON licenses 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create a view for upcoming expirations
CREATE VIEW upcoming_expirations AS
SELECT 
    l.*,
    l.expiration_date - CURRENT_DATE as days_until_expiration
FROM licenses l
WHERE l.expiration_date IS NOT NULL 
    AND l.expiration_date >= CURRENT_DATE
    AND l.expiration_date <= CURRENT_DATE + INTERVAL '35 days'
ORDER BY l.expiration_date ASC;

-- Create a view for licenses needing reminders
CREATE VIEW licenses_needing_reminders AS
WITH reminder_status AS (
    SELECT 
        l.id,
        l.lic_id,
        l.lic_name,
        l.lic_type,
        l.expiration_date,
        l.lic_notify_names,
        l.expiration_date - CURRENT_DATE as days_until_expiration,
        CASE 
            WHEN l.expiration_date - CURRENT_DATE = 30 THEN '30_days'
            WHEN l.expiration_date - CURRENT_DATE = 15 THEN '15_days'
            WHEN l.expiration_date - CURRENT_DATE = 10 THEN '10_days'
            ELSE NULL
        END as reminder_type
    FROM licenses l
    WHERE l.expiration_date IS NOT NULL 
        AND l.lic_notify_names IS NOT NULL
        AND l.lic_notify_names != ''
        AND l.expiration_date >= CURRENT_DATE
        AND l.expiration_date - CURRENT_DATE IN (30, 15, 10)
)
SELECT rs.*
FROM reminder_status rs
LEFT JOIN email_reminders er ON rs.id = er.license_id 
    AND rs.reminder_type = er.reminder_type
    AND DATE(er.sent_date) = CURRENT_DATE
WHERE er.id IS NULL  -- Only get licenses that haven't had reminders sent today
ORDER BY rs.days_until_expiration ASC;

-- Create RLS (Row Level Security) policies if needed
ALTER TABLE licenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_reminders ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated users (adjust as needed)
CREATE POLICY "Enable read access for authenticated users" ON licenses
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Enable all access for authenticated users" ON licenses
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Enable read access for authenticated users" ON email_reminders
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Enable all access for authenticated users" ON email_reminders
    FOR ALL USING (auth.role() = 'authenticated'); 