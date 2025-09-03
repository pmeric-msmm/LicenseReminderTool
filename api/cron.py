"""
Vercel Cron Job for Automatic Email Reminders
This runs daily to check and send license renewal reminders
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the main app and email functions
from api.index import app, query_oracle, ORACLE_CONFIG, COMPANY_INFO
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_licenses_needing_reminders():
    """Get licenses that need reminders today"""
    try:
        schema = ORACLE_CONFIG['schema']
        
        # Get licenses that need reminders
        licenses = query_oracle(f"""
            SELECT 
                l.LIC_ID as id,
                l.LIC_NAME as lic_name,
                l.LIC_TYPE as lic_type,
                l.LIC_STATE as lic_state,
                l.LIC_NO as lic_no,
                l.EXPIRATION_DATE as expiration_date,
                l.LIC_NOTIFY_NAMES as lic_notify_names,
                TRUNC(l.EXPIRATION_DATE) - TRUNC(SYSDATE) as days_until_expiration,
                CASE 
                    WHEN TRUNC(l.EXPIRATION_DATE) - TRUNC(SYSDATE) <= 10 THEN '10_days'
                    WHEN TRUNC(l.EXPIRATION_DATE) - TRUNC(SYSDATE) <= 15 THEN '15_days'
                    WHEN TRUNC(l.EXPIRATION_DATE) - TRUNC(SYSDATE) <= 30 THEN '30_days'
                    ELSE 'custom'
                END as reminder_type
            FROM "{schema}".LICENSES l
            WHERE l.EXPIRATION_DATE IS NOT NULL
            AND l.LIC_NOTIFY_NAMES IS NOT NULL
            AND NVL(l.EMAIL_ENABLED, 1) = 1
            AND (
                -- 30-day reminder
                (TRUNC(l.EXPIRATION_DATE) - TRUNC(SYSDATE) = 30 AND NOT EXISTS (
                    SELECT 1 FROM "{schema}".EMAIL_REMINDERS er
                    WHERE er.LICENSE_ID = l.LIC_ID
                    AND er.REMINDER_TYPE = '30_days'
                    AND TRUNC(er.SENT_DATE) >= TRUNC(SYSDATE) - 7
                ))
                -- 15-day reminder
                OR (TRUNC(l.EXPIRATION_DATE) - TRUNC(SYSDATE) = 15 AND NOT EXISTS (
                    SELECT 1 FROM "{schema}".EMAIL_REMINDERS er
                    WHERE er.LICENSE_ID = l.LIC_ID
                    AND er.REMINDER_TYPE = '15_days'
                    AND TRUNC(er.SENT_DATE) >= TRUNC(SYSDATE) - 7
                ))
                -- 10-day reminder
                OR (TRUNC(l.EXPIRATION_DATE) - TRUNC(SYSDATE) = 10 AND NOT EXISTS (
                    SELECT 1 FROM "{schema}".EMAIL_REMINDERS er
                    WHERE er.LICENSE_ID = l.LIC_ID
                    AND er.REMINDER_TYPE = '10_days'
                    AND TRUNC(er.SENT_DATE) >= TRUNC(SYSDATE) - 7
                ))
                -- 7-day critical reminder
                OR (TRUNC(l.EXPIRATION_DATE) - TRUNC(SYSDATE) = 7 AND NOT EXISTS (
                    SELECT 1 FROM "{schema}".EMAIL_REMINDERS er
                    WHERE er.LICENSE_ID = l.LIC_ID
                    AND er.REMINDER_TYPE = '7_days'
                    AND TRUNC(er.SENT_DATE) >= TRUNC(SYSDATE) - 7
                ))
                -- 1-day urgent reminder
                OR (TRUNC(l.EXPIRATION_DATE) - TRUNC(SYSDATE) = 1 AND NOT EXISTS (
                    SELECT 1 FROM "{schema}".EMAIL_REMINDERS er
                    WHERE er.LICENSE_ID = l.LIC_ID
                    AND er.REMINDER_TYPE = '1_day'
                    AND TRUNC(er.SENT_DATE) >= TRUNC(SYSDATE) - 1
                ))
                -- Overdue reminder (sent once per week)
                OR (TRUNC(l.EXPIRATION_DATE) < TRUNC(SYSDATE) AND NOT EXISTS (
                    SELECT 1 FROM "{schema}".EMAIL_REMINDERS er
                    WHERE er.LICENSE_ID = l.LIC_ID
                    AND er.REMINDER_TYPE = 'overdue'
                    AND TRUNC(er.SENT_DATE) >= TRUNC(SYSDATE) - 7
                ))
            )
        """)
        
        return licenses
    except Exception as e:
        logger.error(f"Error getting licenses needing reminders: {e}")
        return []

def send_reminder_email(license):
    """Send reminder email for a license"""
    try:
        schema = ORACLE_CONFIG['schema']
        
        # Get SMTP configuration
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        sender_email = os.getenv('SENDER_EMAIL', smtp_username)
        
        # Prepare email details
        days_left = license.get('days_until_expiration', 0)
        email_to = license.get('lic_notify_names', '').strip()
        
        if not email_to:
            email_to = COMPANY_INFO['support_email']
        
        # Generate subject based on urgency
        if days_left < 0:
            email_subject = f"⚠️ OVERDUE: {license['lic_name']} - License has EXPIRED"
            urgency_color = '#dc3545'
        elif days_left == 1:
            email_subject = f"🚨 URGENT: {license['lic_name']} - Expires TOMORROW"
            urgency_color = '#dc3545'
        elif days_left <= 7:
            email_subject = f"⚠️ ALERT: {license['lic_name']} - Expires in {days_left} days"
            urgency_color = '#dc3545'
        elif days_left <= 15:
            email_subject = f"📅 REMINDER: {license['lic_name']} - Expires in {days_left} days"
            urgency_color = '#ffc107'
        else:
            email_subject = f"📢 Notice: {license['lic_name']} - Expires in {days_left} days"
            urgency_color = '#17a2b8'
        
        # Generate HTML email body
        email_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {urgency_color}; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-top: none; }}
                .license-info {{ background-color: white; padding: 15px; border-left: 4px solid {urgency_color}; margin: 15px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                .button {{ background-color: {urgency_color}; color: white; padding: 10px 20px; text-decoration: none; display: inline-block; margin: 10px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>License {"EXPIRED" if days_left < 0 else "Expiration Reminder"}</h1>
                </div>
                
                <div class="content">
                    <p>Dear License Administrator,</p>
                    
                    {
                        "<p><strong>⚠️ This license has EXPIRED and requires immediate attention!</strong></p>" 
                        if days_left < 0 
                        else f"<p>This is an automated reminder that the following license will expire in <strong>{days_left} day{'s' if days_left != 1 else ''}</strong>:</p>"
                    }
                    
                    <div class="license-info">
                        <strong>License Holder:</strong> {license.get('lic_name', 'N/A')}<br>
                        <strong>License Type:</strong> {license.get('lic_type', 'N/A')}<br>
                        <strong>State:</strong> {license.get('lic_state', 'N/A')}<br>
                        <strong>License Number:</strong> {license.get('lic_no', 'N/A')}<br>
                        <strong>Expiration Date:</strong> <span style="color: {urgency_color}; font-weight: bold;">{license.get('expiration_date', 'N/A')}</span>
                    </div>
                    
                    <p><strong>Action Required:</strong></p>
                    <ul>
                        <li>{"Renew this license IMMEDIATELY" if days_left <= 0 else "Begin the renewal process if not already started"}</li>
                        <li>Contact the appropriate licensing authority</li>
                        <li>Update our records once renewed</li>
                    </ul>
                    
                    <p>If you have already renewed this license, please update our records or contact support.</p>
                </div>
                
                <div class="footer">
                    <p>This is an automated reminder from {COMPANY_INFO['name']}<br>
                    For assistance, contact: {COMPANY_INFO['support_email']}<br>
                    <a href="{COMPANY_INFO['website']}">{COMPANY_INFO['website']}</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Determine reminder type for logging
        if days_left < 0:
            reminder_type = 'overdue'
        elif days_left == 1:
            reminder_type = '1_day'
        elif days_left == 7:
            reminder_type = '7_days'
        elif days_left == 10:
            reminder_type = '10_days'
        elif days_left == 15:
            reminder_type = '15_days'
        elif days_left == 30:
            reminder_type = '30_days'
        else:
            reminder_type = 'custom'
        
        # Try to send email
        email_status = 'failed'
        
        try:
            if smtp_username and smtp_password:
                msg = MIMEMultipart('alternative')
                msg['From'] = f"{COMPANY_INFO['name']} <{sender_email}>"
                msg['To'] = email_to
                msg['Subject'] = email_subject
                msg.attach(MIMEText(email_body, 'html'))
                
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.send_message(msg)
                
                email_status = 'sent'
                logger.info(f"Email sent successfully for license {license['id']}")
            else:
                logger.warning(f"SMTP not configured, marking as failed for license {license['id']}")
                
        except Exception as e:
            logger.error(f"Failed to send email for license {license['id']}: {e}")
        
        # Always log to EMAIL_REMINDERS table
        query_oracle(f"""
            INSERT INTO "{schema}".EMAIL_REMINDERS (
                LICENSE_ID,
                REMINDER_TYPE,
                EMAIL_TO,
                EMAIL_SUBJECT,
                EMAIL_BODY,
                STATUS,
                SENT_DATE
            ) VALUES (
                :license_id,
                :reminder_type,
                :email_to,
                :email_subject,
                :email_body,
                :status,
                SYSDATE
            )
        """, {
            'license_id': license['id'],
            'reminder_type': reminder_type,
            'email_to': email_to,
            'email_subject': email_subject,
            'email_body': email_body,
            'status': email_status
        })
        
        return email_status == 'sent'
        
    except Exception as e:
        logger.error(f"Error in send_reminder_email: {e}")
        return False

@app.route('/api/cron/check-reminders')
def cron_check_reminders():
    """
    Cron job endpoint to check and send license reminders
    This should be called daily by Vercel Cron
    """
    try:
        # Check if this is a valid cron request (optional security)
        cron_secret = os.getenv('CRON_SECRET')
        if cron_secret:
            request_secret = request.headers.get('Authorization')
            if request_secret != f"Bearer {cron_secret}":
                return jsonify({'error': 'Unauthorized'}), 401
        
        logger.info("Starting automatic reminder check...")
        
        # Get licenses needing reminders
        licenses = get_licenses_needing_reminders()
        
        if not licenses:
            logger.info("No licenses need reminders today")
            return jsonify({
                'success': True,
                'message': 'No licenses need reminders',
                'checked_at': datetime.now().isoformat(),
                'licenses_checked': 0,
                'emails_sent': 0,
                'emails_failed': 0
            })
        
        sent_count = 0
        failed_count = 0
        
        # Send reminders for each license
        for license in licenses:
            if send_reminder_email(license):
                sent_count += 1
            else:
                failed_count += 1
        
        logger.info(f"Reminder check complete: {sent_count} sent, {failed_count} failed")
        
        return jsonify({
            'success': True,
            'message': f'Processed {len(licenses)} licenses',
            'checked_at': datetime.now().isoformat(),
            'licenses_checked': len(licenses),
            'emails_sent': sent_count,
            'emails_failed': failed_count
        })
        
    except Exception as e:
        logger.error(f"Cron job error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'checked_at': datetime.now().isoformat()
        }), 500

# Export for Vercel
handler = app