# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a License Reminder System that manages professional license expirations for MSMM Engineering. It has recently been migrated from Supabase to Oracle Database and includes both a web dashboard and automated email reminder functionality.

## Database Configuration

The system now uses **Oracle Database** (previously Supabase):
- Connection: Uses `SYS` user with SYSDBA privileges
- Schema name: `MSMM DASHBOARD` (note: contains a space, not underscore)
- Main table: `LICENSES`
- Connection module: `oracle_connection.py` with `OracleConnection` class

Critical Oracle notes:
- Schema name must be quoted in SQL: `"MSMM DASHBOARD".LICENSES`
- Uses `oracledb` Python package (successor to cx_Oracle)
- Connection requires SYSDBA mode for SYS user

## Core Components

### Main Applications
1. **license_reminder_system.py**: Original Supabase-based reminder system with scheduler
2. **license_reminder_emailjs.py**: EmailJS integration version for sending reminders
3. **web_dashboard.py**: Flask web dashboard for local development
4. **api/index.py**: Vercel serverless deployment version of dashboard
5. **oracle_connection.py**: Oracle database connection module

### Key Classes
- `LicenseReminderSystem`: Handles Supabase operations and email scheduling
- `LicenseReminderSystemEmailJS`: EmailJS-based reminder system
- `OracleConnection`: Oracle database connection and query handler

## Development Commands

### Virtual Environment Setup
```bash
# Always use .venv for Python development
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# For Oracle support
pip install oracledb
```

### Running the Application
```bash
# Local web dashboard
source .venv/bin/activate && python web_dashboard.py

# With custom port
PORT=8080 python web_dashboard.py

# License reminder checks
python license_reminder_system.py check
python license_reminder_system.py schedule
python license_reminder_system.py upload
```

### Testing Oracle Connection
```bash
source .venv/bin/activate && python oracle_connection.py
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

### Supabase (legacy, still used by some components)
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_ANON_KEY`

### Email Configuration
- `SMTP_SERVER`, `SMTP_PORT`
- `EMAIL_USERNAME`, `EMAIL_PASSWORD`
- `FROM_EMAIL`, `FROM_NAME`

## Deployment

### Vercel Deployment
- Configuration: `vercel.json`
- Entry point: `api/index.py`
- Templates must be in `templates/` directory
- Routes all traffic through serverless function

### Key Files for Deployment
- `vercel.json`: Routing and build configuration
- `requirements.txt`: Python dependencies
- `api/index.py`: Serverless function entry point

## Database Schema

### LICENSES Table Columns
- `LIC_ID`: Unique identifier
- `LIC_NAME`: License holder name
- `LIC_STATE`: State/jurisdiction
- `LIC_TYPE`: License type
- `LIC_NO`: License number
- `EXPIRATION_DATE`: Expiration date
- `LIC_NOTIFY_NAMES`: Email addresses (comma-separated)
- `EMBEDDING`: Vector embeddings for search
- `LIC_FULL_TEXT`: Full text for search

### Email Reminders
System sends reminders at 30, 15, and 10 days before expiration.
Tracks sent reminders to prevent duplicates.

## Common Issues and Solutions

### Oracle Connection Issues
- If getting ORA-01017 (invalid credentials): Check username/password
- If getting ORA-28000 (account locked): Use SYS with SYSDBA
- Schema name has space: Use quoted identifier `"MSMM DASHBOARD"`

### Python Environment
- Always use virtual environment `.venv`
- On macOS, may need `--break-system-packages` flag or use venv
- Install Oracle driver: `pip install oracledb`

### Template Not Found Errors
- Ensure `templates/` directory exists
- For Vercel, check `includeFiles` in `vercel.json`

## Testing & Validation

### Linting and Type Checking
```bash
# No specific linting configured yet
# Recommend adding:
# - ruff for Python linting
# - mypy for type checking
```

### Manual Testing
1. Test Oracle connection: `python oracle_connection.py`
2. Test web dashboard: `python web_dashboard.py`
3. Check API endpoints: `/api/stats`, `/api/upcoming`

## Architecture Notes

The system is transitioning from Supabase to Oracle Database. Current state:
- Oracle connection is working (oracle_connection.py)
- Legacy components still reference Supabase
- Web dashboard (api/index.py) needs updating for Oracle
- Email reminder system needs Oracle integration

Migration priority:
1. Update api/index.py to use OracleConnection
2. Create Oracle-based version of license_reminder_system.py
3. Update EmailJS integration for Oracle
4. Remove Supabase dependencies once migration complete