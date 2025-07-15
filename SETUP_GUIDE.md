# Complete License Reminder System Setup Guide

## 🎯 What You'll Get

✅ **SQL Commands** - Ready to copy/paste into Supabase  
✅ **Free Email Service** - Using EmailJS (no SMTP needed)  
✅ **Web Dashboard** - Beautiful interface to view upcoming expirations  
✅ **Automated Reminders** - 30, 15, and 10 days before expiration  
✅ **Complete Tracking** - Email history and delivery status  

---

## 📋 Step 1: Copy SQL Commands to Supabase

### 1.1 Create Supabase Project
1. Go to [supabase.com](https://supabase.com) and create account
2. Create new project
3. Copy your project URL and API key

### 1.2 Run Database Schema
Copy and paste the contents of `supabase_schema.sql` into your Supabase SQL editor.

### 1.3 Insert Your Excel Data
Copy and paste the contents of `license_data_inserts.sql` into your Supabase SQL editor.

---

## 📧 Step 2: Setup EmailJS (Free Email Service)

### 2.1 Create EmailJS Account
1. Go to [emailjs.com](https://www.emailjs.com/)
2. Sign up for free account (200 emails/month free)

### 2.2 Setup Email Service
1. In EmailJS dashboard, go to **Email Services**
2. Click **Add New Service**
3. Choose your email provider (Gmail recommended)
4. Connect your email account
5. Note your **Service ID**

### 2.3 Create Email Template
1. Go to **Email Templates**
2. Click **Create New Template**
3. Use this template:

```
Subject: {{subject}}

{{message}}

---
From: {{from_name}}
{{company_name}}
Reply to: {{reply_to}}
```

4. Note your **Template ID**

### 2.4 Get API Keys
1. Go to **API Keys**
2. Copy your **Public Key** (User ID)
3. Copy your **Private Key** (optional, for security)

---

## ⚙️ Step 3: Configure Environment

### 3.1 Update .env File
Edit your `.env` file with your actual values:

```env
# Supabase Configuration
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# EmailJS Configuration (Free Email Service)
EMAILJS_SERVICE_ID=your_emailjs_service_id
EMAILJS_TEMPLATE_ID=your_emailjs_template_id
EMAILJS_USER_ID=your_emailjs_public_key
EMAILJS_PRIVATE_KEY=your_emailjs_private_key

# System Configuration
EXCEL_FILE_PATH=licenses.xlsx
TIMEZONE=America/Chicago
PORT=5000
FLASK_DEBUG=false
FLASK_SECRET_KEY=change-this-to-random-string

# Company Information
COMPANY_NAME=MSMM Engineering
COMPANY_WEBSITE=https://www.msmmeng.com
SUPPORT_EMAIL=support@msmmeng.com
FROM_NAME=License Reminder System
```

---

## 🚀 Step 4: Launch the System

### 4.1 Start Web Dashboard
```bash
python3 web_dashboard.py
```
- Access at: http://localhost:5000
- View upcoming expirations
- Monitor email history
- Real-time statistics

### 4.2 Test Email System
```bash
python3 license_reminder_emailjs.py test
```

### 4.3 Run Manual Check
```bash
python3 license_reminder_emailjs.py check
```

### 4.4 Start Automated Scheduler
```bash
python3 license_reminder_emailjs.py schedule
```

---

## 📊 Using the Web Dashboard

### Dashboard Features
- **Statistics Cards**: Overview of license counts
- **Critical Alerts**: Licenses expiring in ≤10 days
- **Warning Alerts**: Licenses expiring in 11-30 days
- **Upcoming**: Licenses expiring in 31-35 days

### Navigation
- **Dashboard**: Main overview
- **All Licenses**: Complete license database
- **Email History**: Sent reminder tracking

### API Endpoints
- `GET /api/upcoming` - Upcoming expirations (JSON)
- `GET /api/stats` - Statistics (JSON)
- `GET /api/license/<id>` - License details (JSON)

---

## 🔄 Data Management

### Adding New Licenses
1. Update your Excel file
2. Run: `python3 license_reminder_emailjs.py upload`

### Email Address Format
In your Excel's `LIC_NOTIFY_NAMES` column:
```
scott@msmmeng.com, philipmeric007@gmail.com
```

---

## 🛠️ Production Deployment

### Option 1: Keep Running (Simple)
```bash
# Terminal 1: Web Dashboard
python3 web_dashboard.py

# Terminal 2: Email Scheduler
python3 license_reminder_emailjs.py schedule
```

### Option 2: Systemd Service (Linux)
Create `/etc/systemd/system/license-dashboard.service`:
```ini
[Unit]
Description=License Dashboard
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/LicenseReminderTool
ExecStart=/usr/bin/python3 web_dashboard.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/license-scheduler.service`:
```ini
[Unit]
Description=License Reminder Scheduler
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/LicenseReminderTool
ExecStart=/usr/bin/python3 license_reminder_emailjs.py schedule
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable services:
```bash
sudo systemctl enable license-dashboard
sudo systemctl enable license-scheduler
sudo systemctl start license-dashboard
sudo systemctl start license-scheduler
```

### Option 3: Cron Job (Email Only)
```bash
# Edit crontab
crontab -e

# Add daily 9 AM check
0 9 * * * cd /path/to/LicenseReminderTool && python3 license_reminder_emailjs.py check
```

---

## 📱 Mobile Access

The web dashboard is responsive and works on:
- Desktop computers
- Tablets
- Mobile phones

---

## 🔍 Monitoring & Logs

### View Logs
```bash
tail -f license_reminders.log
```

### Log Contents
- Upload operations
- Email sending attempts
- Error messages
- Daily statistics

---

## 🚨 Troubleshooting

### Database Issues
```sql
-- Check if data loaded
SELECT COUNT(*) FROM licenses;

-- Check upcoming expirations
SELECT * FROM upcoming_expirations;

-- Check email reminders
SELECT COUNT(*) FROM email_reminders;
```

### Email Issues
1. Verify EmailJS account is active
2. Check email service connection
3. Verify template variables match
4. Test with: `python3 license_reminder_emailjs.py test`

### Web Dashboard Issues
1. Check Supabase connection in `.env`
2. Verify port 5000 is available
3. Check Flask logs in terminal

---

## 📈 System Capabilities

### Current Data Summary
- **52 total licenses** from your Excel file
- **License types**: P.E. Licenses, SAM registrations, SOS filings, etc.
- **States covered**: LA, MS, TX, FL, MI, USA
- **Email contacts**: Already configured for critical licenses

### Reminder Schedule
- **30 days before**: First notification
- **15 days before**: Second notification  
- **10 days before**: Final critical notification

### Email Features
- Professional email templates
- Duplicate prevention (one reminder per day)
- Delivery status tracking
- Multiple recipient support

---

## 🔒 Security Notes

- Keep `.env` file private (never commit to version control)
- EmailJS provides built-in security features
- Supabase handles database security
- Web dashboard runs locally by default

---

## 💡 Pro Tips

1. **Monitor Daily**: Check the dashboard regularly
2. **Update Emails**: Keep contact information current
3. **Regular Backups**: Export license data periodically
4. **Test Regularly**: Run monthly email tests
5. **Mobile Ready**: Access dashboard from phone/tablet

---

## 📞 Support

For issues:
1. Check logs: `tail -f license_reminders.log`
2. Verify configuration in `.env`
3. Test individual components
4. Check Supabase dashboard for database issues

Your license reminder system is now fully operational! 🎉 