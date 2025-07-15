# Vercel Deployment Guide - License Reminder Tool

This guide provides step-by-step instructions for deploying your License Reminder Tool to Vercel using the Vercel UI (dashboard).

## 📋 Prerequisites

Before deploying, ensure you have:

1. **Supabase Database Setup**: Your Supabase project with the following tables:
   - `licenses` - Main license data
   - `upcoming_expirations` - View/table for upcoming expirations
   - `email_reminders` - Email reminder history

2. **GitHub Repository**: Your code should be pushed to a GitHub repository

3. **Vercel Account**: Sign up at [vercel.com](https://vercel.com) (free tier available)

4. **Environment Variables**: Prepare the following values from your Supabase project:
   - `SUPABASE_URL`
   - `SUPABASE_KEY` (anon key)
   - `FLASK_SECRET_KEY`

## 📁 Project Structure

Your project should have this structure after setup:
```
LicenseReminderTool/
├── api/
│   └── index.py          # Main Flask app (serverless function)
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── licenses.html
│   └── reminders.html
├── vercel.json           # Vercel configuration
├── requirements.txt      # Python dependencies
├── config_template.env   # Environment template
└── DEPLOYMENT.md         # This guide
```

## 🚀 Step-by-Step Deployment Process

### Step 1: Prepare Your Repository

1. **Ensure all files are committed and pushed to GitHub**:
   ```bash
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin main
   ```

### Step 2: Login to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Click **"Sign Up"** or **"Login"**
3. Choose **"Continue with GitHub"** to connect your GitHub account
4. Authorize Vercel to access your GitHub repositories

### Step 3: Import Your Project

1. From your Vercel dashboard, click **"New Project"**
2. In the **"Import Git Repository"** section:
   - Find your `LicenseReminderTool` repository
   - Click **"Import"** next to it
3. If you don't see your repository:
   - Click **"Adjust GitHub App Permissions"**
   - Grant access to the repository
   - Return to import screen

### Step 4: Configure Project Settings

1. **Project Name**: 
   - Keep the default or change to something like `license-reminder-dashboard`
   
2. **Framework Preset**: 
   - Select **"Other"** (Vercel will auto-detect Python)
   
3. **Root Directory**: 
   - Leave empty (use root of repository)
   
4. **Build and Output Settings**:
   - **Build Command**: Leave empty (not needed for serverless functions)
   - **Output Directory**: Leave empty
   - **Install Command**: `pip install -r requirements.txt`

### Step 5: Environment Variables Setup

In the **Environment Variables** section, add the following:

| Name | Value | Description |
|------|-------|-------------|
| `SUPABASE_URL` | `https://your-project.supabase.co` | Your Supabase project URL |
| `SUPABASE_KEY` | `your-anon-key` | Your Supabase anon/public key |
| `FLASK_SECRET_KEY` | `your-secret-key-change-this` | Random string for Flask sessions |
| `FLASK_DEBUG` | `false` | Set to false for production |
| `TIMEZONE` | `America/Chicago` | Your timezone (optional) |
| `COMPANY_NAME` | `MSMM Engineering` | Your company name (optional) |
| `COMPANY_WEBSITE` | `https://www.msmmeng.com` | Your website (optional) |
| `SUPPORT_EMAIL` | `support@msmmeng.com` | Support email (optional) |

**How to add environment variables:**
1. Click **"Add"** for each variable
2. Enter the **Name** and **Value**
3. Leave **Environments** as "Production, Preview, Development" (default)

### Step 6: Deploy

1. Click **"Deploy"** button
2. Wait for the build process to complete (usually 1-3 minutes)
3. You'll see build logs in real-time
4. Once successful, you'll get a deployment URL

## 🔧 Build Configuration Details

### Vercel Configuration (`vercel.json`)
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ],
  "env": {
    "PYTHONPATH": "./"
  },
  "functions": {
    "api/index.py": {
      "includeFiles": "templates/**"
    }
  }
}
```

### Python Dependencies (`requirements.txt`)
```
pandas>=2.0.3
openpyxl>=3.1.2
supabase>=1.0.4
python-dotenv>=1.0.0
schedule>=1.2.0
flask>=2.3.0
requests>=2.31.0
```

## 🌐 Post-Deployment

### Accessing Your Application

After successful deployment:
1. **Production URL**: `https://your-project-name.vercel.app`
2. **Custom Domain**: You can add a custom domain in project settings

### Testing Your Deployment

1. Visit your deployment URL
2. Check that the dashboard loads properly
3. Verify Supabase connection by checking if license data displays
4. Test navigation between pages:
   - Dashboard (`/`)
   - Licenses (`/licenses`)
   - Reminders (`/reminders`)

### Monitoring and Logs

1. **Function Logs**: Go to your project dashboard → "Functions" tab
2. **Analytics**: Available in the project overview
3. **Real-time logs**: Click on any function to see recent invocations

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. **Build Fails - Python Dependencies**
**Error**: `Package installation failed`
**Solution**: 
- Check `requirements.txt` for syntax errors
- Ensure all package versions are compatible
- Try removing version constraints temporarily

#### 2. **Runtime Error - Module Not Found**
**Error**: `ModuleNotFoundError: No module named 'X'`
**Solution**:
- Add missing package to `requirements.txt`
- Redeploy the project

#### 3. **Template Not Found**
**Error**: `TemplateNotFound: dashboard.html`
**Solution**:
- Verify `templates/` folder is in repository
- Check `vercel.json` includes templates in `includeFiles`

#### 4. **Supabase Connection Error**
**Error**: `Database not configured` or connection timeouts
**Solution**:
- Verify environment variables are set correctly
- Check Supabase URL format: `https://project-id.supabase.co`
- Ensure anon key is correct (not the service role key)
- Check Supabase project is active and accessible

#### 5. **Environment Variables Not Loading**
**Error**: Variables showing as `None` or default values
**Solution**:
- Check variable names match exactly (case-sensitive)
- Ensure variables are set for all environments
- Redeploy after adding new variables

### Debugging Steps

1. **Check Function Logs**:
   - Go to Vercel dashboard → Project → Functions tab
   - Click on `api/index.py` to see recent logs

2. **Test API Endpoints**:
   - `https://your-app.vercel.app/api/stats`
   - `https://your-app.vercel.app/api/upcoming`

3. **Verify Environment Variables**:
   - Go to Project Settings → Environment Variables
   - Check all required variables are present

## 🔄 Updating Your Application

### For Code Changes

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Update application"
   git push origin main
   ```

2. **Automatic Deployment**: Vercel will automatically redeploy

### For Environment Variable Changes

1. Go to Project Settings → Environment Variables
2. Edit or add new variables
3. Click "Redeploy" to apply changes

## 🔒 Security Considerations

### Environment Variables
- Never commit actual environment variables to GitHub
- Use strong, unique values for `FLASK_SECRET_KEY`
- Keep Supabase keys secure and rotate them periodically

### Supabase Security
- Enable Row Level Security (RLS) on your tables
- Use the anon key (not service role key) for the web app
- Configure proper database policies

## 📊 Performance Optimization

### Cold Starts
- Vercel functions may have cold starts (~1-2 seconds)
- Consider upgrading to Pro plan for improved performance
- Implement proper error handling for timeouts

### Database Queries
- Optimize Supabase queries with proper indexing
- Implement pagination for large datasets
- Cache frequently accessed data

## 🌍 Custom Domain Setup

### Adding a Custom Domain

1. **In Vercel Dashboard**:
   - Go to Project Settings → Domains
   - Click "Add Domain"
   - Enter your domain name

2. **DNS Configuration**:
   - Add CNAME record pointing to `cname.vercel-dns.com`
   - Or A record pointing to Vercel's IP addresses

3. **SSL Certificate**: Automatically provisioned by Vercel

## 💰 Pricing Considerations

### Vercel Free Tier Limits
- **Function Executions**: 125,000/month
- **Function Duration**: 10 seconds max
- **Bandwidth**: 1TB/month
- **Domains**: 100 domains

### When to Upgrade
- High traffic applications
- Need for longer function execution times
- Advanced analytics and monitoring
- Team collaboration features

## 📞 Support Resources

- **Vercel Documentation**: [vercel.com/docs](https://vercel.com/docs)
- **Supabase Documentation**: [supabase.com/docs](https://supabase.com/docs)
- **Flask Documentation**: [flask.palletsprojects.com](https://flask.palletsprojects.com)
- **GitHub Issues**: Create issues in your repository for tracking

---

## 🎉 Congratulations!

Your License Reminder Tool is now deployed on Vercel! The application will automatically scale based on usage and deploy new changes whenever you push to your GitHub repository.

**Quick Access URLs:**
- **Dashboard**: `https://your-app.vercel.app/`
- **Licenses**: `https://your-app.vercel.app/licenses`
- **Reminders**: `https://your-app.vercel.app/reminders`
- **API Stats**: `https://your-app.vercel.app/api/stats`

Remember to bookmark your deployment URL and share it with your team! 