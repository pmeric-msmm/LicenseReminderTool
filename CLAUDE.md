# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a License Reminder System that manages professional license expirations for MSMM Engineering. The system has been successfully migrated from Supabase to Oracle Database and includes both a web dashboard and automated email reminder functionality.

## Database Configuration

The system uses **Oracle Database**:
- Connection: Uses `SYS` user with SYSDBA privileges
- Schema name: `MSMM DASHBOARD` (note: contains a space, not underscore)
- Main table: `LICENSES`
- Connection handling: Direct `oracledb` connections (no separate connection class)

Critical Oracle notes:
- Schema name must be quoted in SQL: `"MSMM DASHBOARD".LICENSES`
- Uses `oracledb` Python package (successor to cx_Oracle)
- Connection requires SYSDBA mode for SYS user

## Core Components

### Main Applications (Oracle-based)
1. **license_reminder_oracle.py**: Main Oracle-based reminder system with scheduler
2. **web_dashboard_oracle.py**: Flask web dashboard for local development
3. **api/index.py**: Vercel serverless deployment version (Oracle-based)
4. **api/cron.py**: Vercel cron job for automated reminders
5. **run_oracle_setup.py**: Oracle database setup automation

### Legacy Components (Supabase-based, kept for reference)
- `license_reminder_system.py`: Original Supabase reminder system
- `license_reminder_emailjs.py`: EmailJS integration version
- `web_dashboard.py`: Original Supabase dashboard
- `api/index_supabase_backup.py`: Backup of Supabase API version

### Key Classes and Files
- `LicenseReminderOracleSystem`: Main Oracle-based reminder system class in `license_reminder_oracle.py`
- Oracle connection utility scripts: `oracle_working_connection.py`, `oracle_test.py`
- Database setup automation: `run_oracle_setup.py`
- SQL DDL scripts: `oracle_setup.sql`

## Development Commands

### Virtual Environment Setup
```bash
# Always use .venv for Python development
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running the Application
```bash
# Local web dashboard (Oracle)
source .venv/bin/activate && python web_dashboard_oracle.py

# With custom port
PORT=5555 python web_dashboard_oracle.py

# License reminder operations (Oracle)
python license_reminder_oracle.py upload
python license_reminder_oracle.py check
python license_reminder_oracle.py schedule
python license_reminder_oracle.py stats
```

### Testing and Debugging
```bash
# Test Oracle connection
source .venv/bin/activate && python oracle_working_connection.py

# Test Oracle setup and views
python oracle_test.py

# Generate SQL inserts for testing
python generate_sql_inserts.py
```

## Environment Variables

Required in `.env` file:

### Oracle Database
- `ORACLE_HOST`: msmm-dashboard.maxapex.net
- `ORACLE_PORT`: 1521
- `ORACLE_SERVICE_NAME`: XEPDB1
- `ORACLE_USER`: SYS
- `ORACLE_PASSWORD`: (DBA password)
- `ORACLE_SCHEMA`: MSMM DASHBOARD
- `ORACLE_TABLE`: LICENSES

### Email Configuration
- `SMTP_SERVER`, `SMTP_PORT`
- `EMAIL_USERNAME`, `EMAIL_PASSWORD`
- `FROM_EMAIL`, `FROM_NAME`

### System Configuration
- `EXCEL_FILE_PATH`: Path to Excel file for data import
- `TIMEZONE`: America/Chicago
- `COMPANY_NAME`, `COMPANY_WEBSITE`, `SUPPORT_EMAIL`
- `FLASK_SECRET_KEY`: Required for Flask sessions

## Deployment

### Vercel Deployment
- Configuration: `vercel.json`
- Entry point: `api/index.py` (Oracle-based)
- Cron job: `api/cron.py` (runs daily at 9 AM)
- Templates must be in `templates/` directory
- Routes all traffic through serverless function
- Automated daily reminder checks via Vercel cron

### Key Files for Deployment
- `vercel.json`: Routing, build configuration, and cron setup
- `requirements.txt`: Python dependencies including `oracledb`
- `api/index.py`: Serverless function entry point (Oracle)
- `api/cron.py`: Automated reminder cron job

## Database Schema

### LICENSES Table (Primary)
- `LIC_ID`: Unique identifier
- `LIC_NAME`: License holder name
- `LIC_STATE`: State/jurisdiction
- `LIC_TYPE`: License type
- `LIC_NO`: License number
- `EXPIRATION_DATE`: Expiration date
- `LIC_NOTIFY_NAMES`: Email addresses (comma-separated)
- `EMAIL_ENABLED`: Controls notification sending
- Additional columns: `ASCEM_NO`, `FIRST_ISSUE_DATE`, `EMBEDDING`, `LIC_FULL_TEXT`

### EMAIL_REMINDERS Table
- Tracks all sent email reminders
- Prevents duplicate reminders on same day
- Links to licenses via `LICENSE_ID`
- Stores email content and delivery status

### Oracle Views
- `LICENSES_NEEDING_REMINDERS`: Identifies licenses requiring reminders today
- `OVERDUE_LICENSES`: Lists expired licenses
- `UPCOMING_EXPIRATIONS`: Shows licenses expiring in next 90 days

### Email Reminder Schedule
System sends reminders at 60, 30, 15, 7, and 1 days before expiration.
Daily reminders are sent for overdue licenses.

## API Endpoints

### Web Dashboard Routes
- `/` - Main dashboard with statistics
- `/licenses` - View and manage all licenses
- `/reminders` - View reminder history
- `/health` - Health check endpoint

### JSON API Routes
- `/api/stats` - System statistics
- `/api/upcoming` - Upcoming expirations
- `/api/cron/check-reminders` - Cron job endpoint

## Common Issues and Solutions

### Oracle Connection Issues
- ORA-01017 (invalid credentials): Check `ORACLE_USER` and `ORACLE_PASSWORD` in `.env`
- ORA-28000 (account locked): Ensure using SYS user with SYSDBA privileges
- ORA-00942 (table/view does not exist): Run `python run_oracle_setup.py`
- Schema name contains space: Always use quoted identifier `"MSMM DASHBOARD"`
- Connection test: Use `python oracle_working_connection.py`

### Python Environment Issues
- Always activate virtual environment: `source .venv/bin/activate`
- Missing dependencies: `pip install -r requirements.txt`
- On macOS: Use virtual environment to avoid system Python conflicts
- Oracle driver installation: `pip install oracledb` (replaces cx_Oracle)

### Development and Deployment Issues
- Template not found: Ensure `templates/` directory exists in project root
- Vercel template issues: Check `includeFiles` in `vercel.json` includes `templates/**`
- Log file access: Check permissions for `license_reminders_oracle.log`
- Email delivery failures: Verify SMTP settings and Gmail app passwords
- Missing environment variables: Ensure all required vars are set in `.env`

## Setup and Migration

### Oracle Database Setup
Run the automated setup script:
```bash
python run_oracle_setup.py
```

This creates:
- `EMAIL_REMINDERS` table for tracking sent emails
- Database views for identifying reminders and expirations
- Proper indexes for query performance

### Data Import from Excel
```bash
python license_reminder_oracle.py upload
```

Excel file format requirements are documented in `README.md`.

## Architecture Notes

The migration from Supabase to Oracle Database is complete:
- ✅ Oracle connection established via `oracle_working_connection.py`
- ✅ Main reminder system migrated (`license_reminder_oracle.py`)
- ✅ Web dashboard migrated (`web_dashboard_oracle.py`)
- ✅ API endpoints migrated (`api/index.py`)
- ✅ Database schema created with views and indexes
- ✅ Vercel deployment configuration updated
- ✅ All 53 licenses successfully migrated

Legacy Supabase components are retained for reference but not actively used.

## Testing Oracle System

### Manual Testing Steps
1. Test Oracle connection: `python oracle_working_connection.py`
2. Test database setup: `python oracle_test.py`
3. Test local dashboard: `python web_dashboard_oracle.py`
4. Test reminder system: `python license_reminder_oracle.py stats`
5. Test data upload: `python license_reminder_oracle.py upload`
6. Verify API endpoints work locally before deploying

### Database Views Testing
```sql
-- Check system statistics
SELECT COUNT(*) FROM "MSMM DASHBOARD".LICENSES;
SELECT COUNT(*) FROM "MSMM DASHBOARD".UPCOMING_EXPIRATIONS;
SELECT COUNT(*) FROM "MSMM DASHBOARD".LICENSES_NEEDING_REMINDERS;
```