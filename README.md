# License Reminder System

An automated license expiration reminder system that sends email notifications 60, 30, 15, 7, and 1 day before license expiration dates. The system uses Oracle Database as the backend and supports Excel file import.

## Features

- ✅ **Oracle Database Integration**: Uses Oracle Database for reliable data storage
- ✅ **Excel Import**: Upload license data from Excel files to Oracle
- ✅ **Automated Reminders**: Send emails 60, 30, 15, 7, and 1 day before expiration
- ✅ **Email Tracking**: Track sent reminders to avoid duplicates
- ✅ **Flexible Email Support**: Support for multiple email addresses per license
- ✅ **Comprehensive Logging**: Detailed logs for monitoring and debugging
- ✅ **Scheduler**: Automated daily checks for upcoming expirations
- ✅ **Database Views**: Smart queries to identify licenses needing reminders
- ✅ **Web Dashboard**: Flask-based web interface for viewing license data
- ✅ **Vercel Deployment Ready**: Serverless function support for cloud deployment

## System Requirements

- Python 3.7 or higher
- Oracle Database (XE or Enterprise Edition)
- Email account with SMTP access (Gmail recommended)
- Virtual environment (recommended)

## Quick Start

### 1. Initial Setup

```bash
# Clone or download the project files
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Edit the `.env` file with your Oracle and email credentials:

```env
# Oracle Database Configuration
ORACLE_HOST=xxxxxxxxxx.xxxxxx.net
ORACLE_PORT=xxxx
ORACLE_SERVICE_NAME=xxxx
ORACLE_USER=SYS
ORACLE_PASSWORD=your_oracle_password
ORACLE_SCHEMA=xxxxxxx
ORACLE_TABLE=LICENSES

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=xxx
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
FROM_EMAIL=your_email@gmail.com
FROM_NAME=License Reminder System

# System Configuration
EXCEL_FILE_PATH=licenses.xlsx
TIMEZONE=America/Chicago

# Company Information
COMPANY_NAME=xxxxxx
COMPANY_WEBSITE=https://www.msmmeng.com
SUPPORT_EMAIL=support@msmmeng.com

# Flask Configuration (for web dashboard)
FLASK_SECRET_KEY=your-secret-key-change-this
FLASK_DEBUG=false
```

### 3. Set Up Oracle Database

Run the setup script to create necessary tables and views:

```bash
python run_oracle_setup.py
```

This will create:
- `EMAIL_REMINDERS` table for tracking sent emails
- `LICENSES_NEEDING_REMINDERS` view for identifying licenses requiring reminders
- `OVERDUE_LICENSES` view for expired licenses
- `UPCOMING_EXPIRATIONS` view for licenses expiring soon

### 4. Upload License Data

```bash
python license_reminder_oracle.py upload
```

### 5. Test the System

```bash
# Check system statistics
python license_reminder_oracle.py stats

# Run a one-time check for reminders
python license_reminder_oracle.py check
```

### 6. Start Automated Scheduler

```bash
# Start the daily scheduler (runs at 9:00 AM daily)
python license_reminder_oracle.py schedule
```

## Web Dashboard

### Local Development

```bash
# Run the Flask web dashboard
python web_dashboard_oracle.py

# Access at http://localhost:8080
# Or specify a custom port:
PORT=5000 python web_dashboard_oracle.py
```

### Vercel Deployment

The application is ready for serverless deployment on Vercel:

1. Push your code to GitHub
2. Import the project in Vercel
3. Set environment variables in Vercel dashboard
4. Deploy

The API endpoints will be available at:
- `/` - Main dashboard
- `/licenses` - View all licenses
- `/reminders` - Reminder history
- `/api/stats` - JSON statistics
- `/api/upcoming` - Upcoming expirations
- `/health` - Health check endpoint

## Excel File Format

Your Excel file should contain the following columns:

| Column Name | Type | Description | Required |
|-------------|------|-------------|----------|
| LIC_ID | Integer | Unique license identifier | Yes |
| LIC_NAME | Text | License holder name | Yes |
| LIC_STATE | Text | State/jurisdiction | No |
| LIC_TYPE | Text | Type of license | No |
| LIC_NO | Text | License number | No |
| ASCEM_NO | Number | ASCEM number | No |
| FIRST_ISSUE_DATE | Date | Date first issued | No |
| EXPIRATION_DATE | Date | License expiration date | No |
| LIC_NOTIFY_NAMES | Text | Email addresses (comma-separated) | No |

### Email Format in Excel

For multiple email addresses in the `LIC_NOTIFY_NAMES` column, separate them with commas:

```
john@company.com, jane@company.com, admin@company.com
```

## Database Schema

### Oracle Tables

#### `LICENSES` Table
- Stores all license information from Excel
- Primary key: `LIC_ID`
- Includes embedding columns for future AI features

#### `EMAIL_REMINDERS` Table
- Tracks all sent reminders
- Prevents duplicate reminders on the same day
- Links to licenses via `LICENSE_ID`
- Stores email content and delivery status

### Oracle Views

- `UPCOMING_EXPIRATIONS`: Licenses expiring in the next 90 days
- `LICENSES_NEEDING_REMINDERS`: Licenses requiring reminders today
- `OVERDUE_LICENSES`: Expired licenses

## Usage Commands

### Oracle Version Commands

```bash
# Upload Excel data
python license_reminder_oracle.py upload

# Check statistics
python license_reminder_oracle.py stats

# Run one-time reminder check
python license_reminder_oracle.py check

# Start automated scheduler
python license_reminder_oracle.py schedule
```

### Web Dashboard

```bash
# Run local web dashboard
python web_dashboard_oracle.py
```

## Email Configuration

### Gmail Setup (Recommended)

1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Select "Mail" and generate a password
   - Use this password in the EMAIL_PASSWORD field

### Other Email Providers

Update the SMTP settings in `.env`:
- **Outlook/Hotmail**: `smtp-mail.outlook.com:587`
- **Yahoo**: `smtp.mail.yahoo.com:587`
- **Custom SMTP**: Check your provider's documentation

## Logging

The system creates detailed logs:
- `license_reminders_oracle.log` - Oracle version logs
- All operations (upload, reminder checks, email sending)
- Errors and exceptions
- Timestamp for each action
- Email delivery confirmations

### Checking Logs

```bash
# View recent log entries
tail -f license_reminders_oracle.log

# View all logs
cat license_reminders_oracle.log
```

## Database Queries

### Oracle SQL Queries

```sql
-- Check upcoming expirations
SELECT * FROM "MSMM DASHBOARD".UPCOMING_EXPIRATIONS;

-- View sent reminders
SELECT * FROM "MSMM DASHBOARD".EMAIL_REMINDERS 
ORDER BY SENT_DATE DESC;

-- Check licenses without email addresses
SELECT * FROM "MSMM DASHBOARD".LICENSES 
WHERE LIC_NOTIFY_NAMES IS NULL;

-- Check licenses needing reminders
SELECT * FROM "MSMM DASHBOARD".LICENSES_NEEDING_REMINDERS;
```

## Troubleshooting

### Common Issues

**"No module named 'oracledb'"**
```bash
pip install -r requirements.txt
# or
pip install oracledb
```

**"ORA-01017: invalid credential"**
- Verify Oracle username and password in `.env`
- Ensure using SYS user with SYSDBA privileges
- Check if account is locked

**"ORA-00942: table or view does not exist"**
- Run `python run_oracle_setup.py` to create views
- Check schema name (note: "MSMM DASHBOARD" has a space)

**"Missing required environment variables"**
- Check that `.env` file exists and contains all required values
- Ensure ORACLE_HOST, ORACLE_PASSWORD, EMAIL_USERNAME, EMAIL_PASSWORD are set

**"Email sending failed"**
- Verify SMTP settings
- For Gmail, ensure you're using an App Password
- Check firewall/network restrictions

**"No licenses need reminders today"**
- This is normal if no licenses match reminder criteria (60, 30, 15, 7, 1 days)
- Check the `UPCOMING_EXPIRATIONS` view to see upcoming expirations

## Production Deployment

### Using systemd (Linux)

Create a service file `/etc/systemd/system/license-reminders.service`:

```ini
[Unit]
Description=License Reminder System (Oracle)
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/license-reminder-system
Environment="PATH=/path/to/.venv/bin"
ExecStart=/path/to/.venv/bin/python license_reminder_oracle.py schedule
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable license-reminders
sudo systemctl start license-reminders
```

### Using cron

Add a daily cron job:
```bash
# Edit crontab
crontab -e

# Add this line for daily 9 AM execution
0 9 * * * cd /path/to/license-reminder-system && /path/to/.venv/bin/python license_reminder_oracle.py check
```

## Security Considerations

- Store sensitive credentials in environment variables, not in code
- Use Oracle database security features (user roles, privileges)
- Regularly rotate passwords and API keys
- Monitor logs for unauthorized access attempts
- Use secure connections (SSL/TLS) when possible
- Never commit `.env` file to version control

## File Structure

```
LicenseReminderTool/
├── api/
│   └── index.py              # Vercel serverless function (Oracle)
├── templates/
│   ├── base.html            # Base template
│   ├── dashboard.html       # Dashboard view
│   ├── licenses.html        # Licenses view
│   └── reminders.html       # Reminders view
├── license_reminder_oracle.py    # Main Oracle reminder system
├── web_dashboard_oracle.py       # Flask web dashboard
├── run_oracle_setup.py          # Oracle setup script
├── oracle_setup.sql             # Oracle DDL scripts
├── requirements.txt             # Python dependencies
├── vercel.json                  # Vercel configuration
├── .env                         # Environment variables (not in git)
└── README.md                    # This file
```

## Migration from Supabase

If migrating from the Supabase version:
1. Export data from Supabase using the Excel export feature
2. Update `.env` with Oracle credentials
3. Run `python run_oracle_setup.py` to set up Oracle
4. Run `python license_reminder_oracle.py upload` to import data

## Support

For questions or issues:

1. Check the troubleshooting section above
2. Review the logs in `license_reminders_oracle.log`
3. Verify your configuration in `.env`
4. Check Oracle database connectivity
5. Ensure all required views are created

## License

This project is provided as-is for internal use. Modify and distribute according to your organization's requirements.

PORT=5555 python web_dashboard_oracle.py
