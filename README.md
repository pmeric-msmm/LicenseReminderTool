# License Reminder System

An automated license expiration reminder system that sends email notifications 30, 15, and 10 days before license expiration dates. The system uses Supabase as the database backend and supports Excel file import.

## Features

- ✅ **Excel Import**: Upload license data from Excel files to Supabase
- ✅ **Automated Reminders**: Send emails 30, 15, and 10 days before expiration
- ✅ **Email Tracking**: Track sent reminders to avoid duplicates
- ✅ **Flexible Email Support**: Support for multiple email addresses per license
- ✅ **Comprehensive Logging**: Detailed logs for monitoring and debugging
- ✅ **Scheduler**: Automated daily checks for upcoming expirations
- ✅ **Database Views**: Smart queries to identify licenses needing reminders

## System Requirements

- Python 3.7 or higher
- Supabase account
- Email account with SMTP access (Gmail recommended)

## Quick Start

### 1. Initial Setup

```bash
# Clone or download the project files
# Ensure you have licenses.xlsx in the project directory

# Run the setup script
python3 setup.py
```

### 2. Configure Environment Variables

Edit the `.env` file created by the setup script:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
FROM_EMAIL=your_email@gmail.com
FROM_NAME=License Reminder System

# System Configuration
EXCEL_FILE_PATH=licenses.xlsx
TIMEZONE=America/Chicago

# Company Information
COMPANY_NAME=MSMM Engineering
COMPANY_WEBSITE=https://www.msmmeng.com
SUPPORT_EMAIL=support@msmmeng.com
```

### 3. Set Up Supabase Database

1. Create a new Supabase project at [supabase.com](https://supabase.com)
2. Copy your project URL and anon key to the `.env` file
3. In the Supabase SQL editor, run the commands from `supabase_schema.sql`

### 4. Upload License Data

```bash
python3 license_reminder_system.py upload
```

### 5. Test the System

```bash
# Run a one-time check for reminders
python3 license_reminder_system.py check
```

### 6. Start Automated Scheduler

```bash
# Start the daily scheduler (runs at 9:00 AM daily)
python3 license_reminder_system.py schedule
```

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

The system creates two main tables:

### `licenses` Table
- Stores all license information from the Excel file
- Includes timestamps for tracking updates
- Primary key: `id` (auto-generated)
- Unique constraint on `lic_id`

### `email_reminders` Table
- Tracks all sent reminders
- Prevents duplicate reminders on the same day
- Links to licenses table via foreign key
- Stores email content and delivery status

### Useful Views
- `upcoming_expirations`: Licenses expiring in the next 35 days
- `licenses_needing_reminders`: Licenses requiring reminders today

## Usage Commands

### Upload Excel Data
```bash
python3 license_reminder_system.py upload
```
- Reads the Excel file specified in EXCEL_FILE_PATH
- Inserts new records and updates existing ones
- Avoids duplicates based on LIC_ID

### Run One-Time Check
```bash
python3 license_reminder_system.py check
```
- Checks for licenses needing reminders today
- Sends emails immediately
- Useful for testing and manual runs

### Start Scheduler
```bash
python3 license_reminder_system.py schedule
```
- Starts the automated daily scheduler
- Runs reminder checks at 9:00 AM daily
- Continues running until stopped (Ctrl+C)

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

The system creates detailed logs in `license_reminders.log`:

- All operations (upload, reminder checks, email sending)
- Errors and exceptions
- Timestamp for each action
- Email delivery confirmations

## Troubleshooting

### Common Issues

**"No module named 'supabase'"**
```bash
pip3 install -r requirements.txt
```

**"Missing required environment variables"**
- Check that `.env` file exists and contains all required values
- Ensure SUPABASE_URL, SUPABASE_KEY, EMAIL_USERNAME, EMAIL_PASSWORD, and FROM_EMAIL are set

**"Error uploading Excel data"**
- Verify Excel file exists and is readable
- Check Supabase URL and API key
- Ensure database schema has been created

**"Email sending failed"**
- Verify SMTP settings
- For Gmail, ensure you're using an App Password
- Check firewall/network restrictions

**"No licenses need reminders today"**
- This is normal if no licenses are expiring in 30, 15, or 10 days
- Check the `upcoming_expirations` view in Supabase to see upcoming expirations

### Checking Logs

```bash
# View recent log entries
tail -f license_reminders.log

# View all logs
cat license_reminders.log
```

## Database Queries

### Check Upcoming Expirations
```sql
SELECT * FROM upcoming_expirations;
```

### View Sent Reminders
```sql
SELECT * FROM email_reminders ORDER BY sent_date DESC;
```

### Check Licenses Without Email Addresses
```sql
SELECT * FROM licenses 
WHERE lic_notify_names IS NULL OR lic_notify_names = '';
```

## Production Deployment

### Using systemd (Linux)

Create a service file `/etc/systemd/system/license-reminders.service`:

```ini
[Unit]
Description=License Reminder System
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/license-reminder-system
ExecStart=/usr/bin/python3 license_reminder_system.py schedule
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
0 9 * * * cd /path/to/license-reminder-system && python3 license_reminder_system.py check
```

## Security Considerations

- Store sensitive credentials in environment variables, not in code
- Use Supabase Row Level Security (RLS) policies for data protection
- Regularly rotate API keys and passwords
- Monitor logs for unauthorized access attempts
- Use HTTPS for all Supabase connections

## Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For questions or issues:

1. Check the troubleshooting section above
2. Review the logs in `license_reminders.log`
3. Verify your configuration in `.env`
4. Check Supabase dashboard for database issues

## License

This project is provided as-is for internal use. Modify and distribute according to your organization's requirements. 



PORT=8080 python3 web_dashboard.py