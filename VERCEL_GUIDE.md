# Vercel Deployment Guide for License Reminder Dashboard

This guide provides detailed step-by-step instructions for deploying the License Reminder Dashboard to Vercel using the **Web UI** (not CLI).

## 🎯 Key Features After Deployment
- ✅ **Automatic Daily Email Reminders** - Runs at 9:00 AM UTC daily
- ✅ Web Dashboard for License Management
- ✅ Email History Tracking
- ✅ Manual Email Sending
- ✅ CRUD Operations for Licenses

## Prerequisites

Before deploying, ensure you have:
1. A GitHub account with this repository pushed to it
2. A Vercel account (free tier works fine)
3. Oracle Database credentials and connection details
4. SMTP credentials (optional, for email functionality)

## Step 1: Prepare Your Repository

### 1.1 Push to GitHub
```bash
git add .
git commit -m "Ready for Vercel deployment"
git push origin main
```

### 1.2 Verify Required Files
Ensure these files exist in your repository root:
- ✅ `vercel.json` - Vercel configuration
- ✅ `requirements.txt` - Python dependencies  
- ✅ `api/index.py` - Main application file
- ✅ `templates/` - HTML templates directory
- ✅ `static/` - Static files directory (if any)
- ✅ `.env.example` - Environment variables template

## Step 2: Create Vercel Account

1. Go to [https://vercel.com](https://vercel.com)
2. Click **"Sign Up"**
3. Choose **"Continue with GitHub"** (recommended)
4. Authorize Vercel to access your GitHub account

## Step 3: Import Project to Vercel

### 3.1 Start Import Process
1. Log into Vercel Dashboard
2. Click **"Add New..."** → **"Project"**
3. Click **"Import Git Repository"**

### 3.2 Connect GitHub Repository
1. If not connected, click **"Add GitHub Account"**
2. Select your GitHub account
3. Choose **"All repositories"** or **"Only select repositories"**
4. Find and select **"LicenseReminderTool"** repository
5. Click **"Import"**

## Step 4: Configure Build & Development Settings

### 4.1 Framework Preset
- **Framework Preset**: Select **"Other"**
- **Root Directory**: Leave as `./` (unless in a subdirectory)

### 4.2 Build and Output Settings
- **Build Command**: Leave empty or use `pip install -r requirements.txt`
- **Output Directory**: Leave as default
- **Install Command**: Leave as default

### 4.3 Node.js Version
- Keep default (not applicable for Python)

## Step 5: Configure Environment Variables

This is the **MOST IMPORTANT** step. Click on **"Environment Variables"** and add the following:

### 5.1 Oracle Database Variables (REQUIRED)
| Variable Name | Value | Description |
|--------------|--------|-------------|
| `ORACLE_HOST` | `xxxxxxxxxx.xxxxxx.net` | Your Oracle host |
| `ORACLE_PORT` | `xxx1` | Oracle port (usually 1521) |
| `ORACLE_SERVICE_NAME` | `xxxxx` | Your Oracle service name |
| `ORACLE_USER` | `SYS` | Oracle username |
| `ORACLE_PASSWORD` | `[Your Password]` | Oracle password |
| `ORACLE_SCHEMA` | `xxxxxxxx` | Schema name (with space) |
| `ORACLE_TABLE` | `LICENSES` | Main table name |

### 5.2 Flask Configuration (REQUIRED)
| Variable Name | Value | Description |
|--------------|--------|-------------|
| `FLASK_SECRET_KEY` | `[Generate a random string]` | Flask session secret |
| `FLASK_DEBUG` | `False` | Keep False for production |

### 5.3 Company Information (OPTIONAL but Recommended)
| Variable Name | Value | Description |
|--------------|--------|-------------|
| `COMPANY_NAME` | `xxxxxxxxxx` | Your company name |
| `COMPANY_WEBSITE` | `https://www.msmmeng.com` | Company website |
| `SUPPORT_EMAIL` | `support@msmmeng.com` | Support email |

### 5.4 Email Configuration (REQUIRED for automatic reminders)

**IMPORTANT**: These are required if you want automatic daily email reminders to work!
| Variable Name | Value | Description |
|--------------|--------|-------------|
| `SMTP_SERVER` | `smtp.gmail.com` | SMTP server address |
| `SMTP_PORT` | `xxxx` | SMTP port |
| `SMTP_USERNAME` | `your-email@gmail.com` | SMTP username |
| `SMTP_PASSWORD` | `[App Password]` | SMTP password/app password |
| `SENDER_EMAIL` | `your-email@gmail.com` | From email address |
| `FROM_NAME` | `License Reminder System` | From name |

### 5.5 How to Add Environment Variables in Vercel UI:
1. In the Environment Variables section, click **"Add"**
2. Enter the **Name** (e.g., `ORACLE_HOST`)
3. Enter the **Value** (e.g., `xxxxxxxxx.xxxxxx.net`)
4. Select environments: ✅ Production, ✅ Preview, ✅ Development
5. Click **"Add"** to save
6. Repeat for all variables

**⚠️ IMPORTANT**: 
- Double-check all values before deploying
- Oracle password and SMTP passwords are sensitive - ensure they're correct
- Use the **eye icon** to show/hide sensitive values
- For `ORACLE_SCHEMA`, include the space if your schema is "MSMM DASHBOARD"

## Step 6: Deploy

1. After adding all environment variables, click **"Deploy"**
2. Vercel will start the deployment process
3. You'll see build logs in real-time
4. Deployment typically takes 1-3 minutes

### 5.5 Cron Job Security (OPTIONAL but Recommended)
| Variable Name | Value | Description |
|--------------|--------|-------------|
| `CRON_SECRET` | `[Generate a random string]` | Secret key to protect cron endpoint |

Add this to prevent unauthorized access to your cron job endpoint.

## Step 6A: Configure Automatic Email Reminders (Cron Job)

### Enable Daily Automatic Email Checks
Vercel will automatically run the email reminder check **daily at 9:00 AM UTC** based on the configuration in `vercel.json`.

The cron job will:
- Check for licenses expiring in 30, 15, 10, 7, and 1 days
- Send email reminders to configured recipients
- Log all attempts in the EMAIL_REMINDERS table
- Prevent duplicate emails (won't send same reminder within 7 days)

### Cron Schedule Explanation:
- `"0 9 * * *"` = Every day at 9:00 AM UTC
- To change the time, modify the schedule in `vercel.json`
- Use [crontab.guru](https://crontab.guru) to generate custom schedules

### Manual Trigger:
You can manually trigger the reminder check:
```
https://your-app.vercel.app/api/cron/check-reminders
```

### Monitor Cron Jobs:
1. Go to Vercel Dashboard → Your Project
2. Click on **"Functions"** tab
3. Click on **"Crons"** sub-tab
4. View execution history and logs

## Step 7: Verify Deployment

### 7.1 Check Build Status
- ✅ **"Ready"** status means successful deployment
- ❌ **"Error"** means check the build logs

### 7.2 Access Your Application
1. Click on the deployment URL (e.g., `license-reminder-tool.vercel.app`)
2. You should see the License Dashboard homepage

### 7.3 Test Functionality
1. Check if the dashboard loads
2. Verify database connection (licenses should appear)
3. Test filtering and search
4. Check email history page

## Step 8: Custom Domain (Optional)

### 8.1 Add Custom Domain
1. Go to Project Settings → Domains
2. Click **"Add"**
3. Enter your domain (e.g., `licenses.msmmeng.com`)
4. Follow DNS configuration instructions

### 8.2 DNS Configuration
Add these records to your domain's DNS:
- **A Record**: Point to Vercel's IP
- **CNAME**: Point to `cname.vercel-dns.com`

## Troubleshooting

### Common Issues and Solutions

#### 1. Oracle Connection Error
**Error**: "Oracle connection error: DPY-1001"
**Solution**: 
- Verify Oracle credentials in environment variables
- Check if Oracle server allows external connections
- Ensure `ORACLE_SCHEMA` includes quotes if it has spaces

#### 2. Module Import Error
**Error**: "No module named 'oracledb'"
**Solution**:
- Ensure `requirements.txt` includes `oracledb>=2.0.0`
- Rebuild the deployment

#### 3. Template Not Found
**Error**: "TemplateNotFoundError"
**Solution**:
- Verify `templates/` folder is in repository
- Check `vercel.json` includes template files

#### 4. 500 Internal Server Error
**Solution**:
1. Check Vercel Function Logs:
   - Go to Functions tab in Vercel dashboard
   - Click on the function
   - View real-time logs
2. Common causes:
   - Missing environment variables
   - Database connection issues
   - SMTP configuration errors

#### 5. Static Files Not Loading
**Solution**:
- Ensure static files are in `static/` directory
- Update `vercel.json` routes if needed

## Monitoring & Logs

### View Logs in Vercel Dashboard:
1. Go to your project in Vercel
2. Click on **"Functions"** tab
3. Click on `api/index` function
4. View **"Realtime Logs"**

### Enable Detailed Logging:
Add environment variable:
- `LOG_LEVEL`: `DEBUG`

## Updating the Application

### To Deploy Updates:
1. Make changes in your local repository
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update description"
   git push origin main
   ```
3. Vercel automatically deploys on push to main branch

### Manual Redeploy:
1. Go to Vercel dashboard
2. Click on your project
3. Go to **"Deployments"** tab
4. Click **"Redeploy"** on any deployment

## Security Best Practices

1. **Never commit `.env` file** to repository
2. Use **environment variables** for all sensitive data
3. Rotate database passwords regularly
4. Use app-specific passwords for SMTP
5. Enable 2FA on Vercel and GitHub accounts
6. Regularly update dependencies in `requirements.txt`

## Performance Optimization

### Vercel Configuration Options:
Update `vercel.json` for better performance:

```json
{
  "functions": {
    "api/index.py": {
      "maxDuration": 30,
      "memory": 1024
    }
  }
}
```

### Database Connection Pooling:
Consider implementing connection pooling for better performance with multiple concurrent users.

## Support & Resources

- **Vercel Documentation**: https://vercel.com/docs
- **Python on Vercel**: https://vercel.com/docs/runtimes/python
- **Oracle Database**: https://python-oracledb.readthedocs.io/
- **Flask Documentation**: https://flask.palletsprojects.com/

## Deployment Checklist

Before deploying, ensure:
- [ ] All code committed to GitHub
- [ ] Environment variables documented
- [ ] Oracle database accessible from internet
- [ ] SMTP credentials ready (if using email)
- [ ] Tested locally with production data
- [ ] Backup of database created
- [ ] `requirements.txt` up to date
- [ ] `vercel.json` configured correctly
- [ ] Templates and static files included

## Final Notes

- **Free Tier Limits**: Vercel free tier includes 100GB bandwidth and 100 hours of function execution
- **Scaling**: Application automatically scales with Vercel's infrastructure
- **Region Selection**: Choose region closest to your Oracle database for best performance
- **Backup Strategy**: Implement regular database backups separately

---

**Successfully deployed?** Your License Reminder Dashboard should now be live on Vercel! 🎉

For issues or questions, check the logs in Vercel dashboard or review this guide.
