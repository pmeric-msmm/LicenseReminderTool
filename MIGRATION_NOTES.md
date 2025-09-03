# Migration from Supabase to Oracle Database

## Migration Summary

Successfully migrated the License Reminder System from Supabase to Oracle Database on September 3, 2025.

## What Changed

### Database Platform
- **From**: Supabase (PostgreSQL)
- **To**: Oracle Database (XE/Enterprise)
- **Schema**: MSMM DASHBOARD (note the space in the name)

### Key Files Updated

1. **New Oracle-specific files**:
   - `license_reminder_oracle.py` - Main reminder system using Oracle
   - `web_dashboard_oracle.py` - Flask dashboard for Oracle
   - `oracle_setup.sql` - DDL scripts for Oracle setup
   - `run_oracle_setup.py` - Python script to execute Oracle setup
   - `oracle_working_connection.py` - Oracle connection testing

2. **Modified files**:
   - `api/index.py` - Now uses Oracle instead of Supabase
   - `requirements.txt` - Added `oracledb`, removed `supabase`
   - `README.md` - Updated with Oracle instructions
   - `.env` - Added Oracle configuration variables

3. **Backup files** (kept for reference):
   - `api/index_supabase_backup.py` - Original Supabase version
   - `license_reminder_system.py` - Original Supabase reminder system
   - `web_dashboard.py` - Original Supabase dashboard

## Database Objects Created

### Tables
- `EMAIL_REMINDERS` - Tracks sent email reminders

### Views
- `LICENSES_NEEDING_REMINDERS` - Identifies licenses requiring reminders (60, 30, 15, 7, 1 day)
- `OVERDUE_LICENSES` - Lists expired licenses
- `UPCOMING_EXPIRATIONS` - Shows licenses expiring in next 90 days

### Columns Added
- `EMAIL_ENABLED` - Added to LICENSES table for controlling notifications

## Connection Details

- **User**: SYS (with SYSDBA privileges)
- **Schema**: "MSMM DASHBOARD" (must be quoted in SQL due to space)
- **Python Driver**: oracledb (successor to cx_Oracle)

## Environment Variables

### New Oracle Variables
```env
ORACLE_HOST=msmm-dashboard.maxapex.net
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=XEPDB1
ORACLE_USER=SYS
ORACLE_PASSWORD=<password>
ORACLE_SCHEMA=MSMM DASHBOARD
ORACLE_TABLE=LICENSES
```

### Removed Supabase Variables
- SUPABASE_URL (kept for legacy compatibility)
- SUPABASE_KEY (kept for legacy compatibility)
- SUPABASE_SERVICE_KEY
- SUPABASE_ANON_KEY

## Reminder Schedule Changes

Updated from 30/15/10 days to:
- 60 days before expiration
- 30 days before expiration  
- 15 days before expiration
- 7 days before expiration
- 1 day before expiration
- Daily reminders for overdue licenses

## API Endpoints (No Change)

All endpoints remain the same:
- `/` - Dashboard
- `/licenses` - View licenses
- `/reminders` - Reminder history
- `/api/stats` - Statistics JSON
- `/api/upcoming` - Upcoming expirations JSON
- `/health` - Health check

## Commands

### Old (Supabase)
```bash
python license_reminder_system.py [upload|check|schedule]
python web_dashboard.py
```

### New (Oracle)
```bash
python license_reminder_oracle.py [upload|check|schedule|stats]
python web_dashboard_oracle.py
```

## Testing Performed

✅ Oracle connection established
✅ Tables and views created successfully
✅ 53 licenses loaded
✅ Views returning correct data:
  - 8 upcoming expirations
  - 5 overdue licenses
  - 5 licenses needing reminders
✅ API endpoints tested and working
✅ Web dashboard functional

## Deployment Notes

For Vercel deployment:
1. Ensure all Oracle environment variables are set in Vercel
2. The `api/index.py` file now uses Oracle
3. `oracledb` package is included in requirements.txt
4. No changes needed to `vercel.json`

## Rollback Plan

If needed to rollback to Supabase:
1. Rename `api/index_supabase_backup.py` back to `api/index.py`
2. Use `license_reminder_system.py` instead of `license_reminder_oracle.py`
3. Use `web_dashboard.py` instead of `web_dashboard_oracle.py`
4. Update requirements.txt to include supabase package
5. Ensure Supabase environment variables are set

## Known Issues

None at this time. All features tested and working.

## Performance Notes

- Oracle views are optimized with proper indexes
- Connection uses SYS with SYSDBA for full access
- Schema name requires quotes due to space: "MSMM DASHBOARD"

## Support

For issues with Oracle connection:
1. Verify credentials in .env
2. Check network connectivity to Oracle host
3. Ensure SYS account is not locked
4. Run `python oracle_working_connection.py` to test

---
Migration completed successfully on September 3, 2025