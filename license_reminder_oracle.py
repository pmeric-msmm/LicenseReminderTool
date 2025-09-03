"""
License Reminder System - Oracle Database Version
Automated email reminders for license expirations using Oracle DB
"""

import os
import sys
import logging
import schedule
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import oracledb
import pandas as pd

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('license_reminders_oracle.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LicenseReminderOracleSystem:
    """Oracle-based License Reminder System"""
    
    def __init__(self):
        """Initialize the Oracle License Reminder System"""
        self.validate_environment_variables()
        self.setup_oracle_connection()
        self.setup_email_config()
        
    def validate_environment_variables(self):
        """Validate that all required environment variables are set"""
        required_vars = [
            'ORACLE_HOST', 'ORACLE_PORT', 'ORACLE_SERVICE_NAME',
            'ORACLE_PASSWORD', 'ORACLE_SCHEMA', 'ORACLE_TABLE',
            'EMAIL_USERNAME', 'EMAIL_PASSWORD', 'FROM_EMAIL', 'FROM_NAME',
            'SMTP_SERVER', 'SMTP_PORT'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    def setup_oracle_connection(self):
        """Setup Oracle database connection parameters"""
        self.oracle_config = {
            'host': os.getenv('ORACLE_HOST'),
            'port': int(os.getenv('ORACLE_PORT', 1521)),
            'service': os.getenv('ORACLE_SERVICE_NAME'),
            'user': os.getenv('ORACLE_USER', 'SYS'),
            'password': os.getenv('ORACLE_PASSWORD'),
            'schema': os.getenv('ORACLE_SCHEMA'),
            'table': os.getenv('ORACLE_TABLE')
        }
        logger.info("Oracle connection parameters configured")
    
    def setup_email_config(self):
        """Setup email configuration"""
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587)),
            'username': os.getenv('EMAIL_USERNAME'),
            'password': os.getenv('EMAIL_PASSWORD'),
            'from_email': os.getenv('FROM_EMAIL'),
            'from_name': os.getenv('FROM_NAME', 'License Reminder System')
        }
        
        # Company information for email templates
        self.company_info = {
            'name': os.getenv('COMPANY_NAME', 'MSMM Engineering'),
            'website': os.getenv('COMPANY_WEBSITE', 'https://www.msmmeng.com'),
            'support_email': os.getenv('SUPPORT_EMAIL', 'support@msmmeng.com')
        }
        logger.info("Email configuration loaded")
    
    def get_oracle_connection(self):
        """Create and return an Oracle database connection"""
        try:
            dsn = oracledb.makedsn(
                self.oracle_config['host'],
                self.oracle_config['port'],
                service_name=self.oracle_config['service']
            )
            
            connection = oracledb.connect(
                user=self.oracle_config['user'],
                password=self.oracle_config['password'],
                dsn=dsn,
                mode=oracledb.AUTH_MODE_SYSDBA
            )
            
            return connection
        except oracledb.Error as e:
            logger.error(f"Oracle connection error: {e}")
            raise
    
    def upload_excel_data(self, excel_path: str = None):
        """Upload license data from Excel to Oracle database"""
        if not excel_path:
            excel_path = os.getenv('EXCEL_FILE_PATH', 'licenses.xlsx')
        
        if not os.path.exists(excel_path):
            logger.error(f"Excel file not found: {excel_path}")
            return False
        
        try:
            # Read Excel file
            df = pd.read_excel(excel_path)
            logger.info(f"Read {len(df)} rows from Excel file")
            
            # Connect to Oracle
            connection = self.get_oracle_connection()
            cursor = connection.cursor()
            
            schema = self.oracle_config['schema']
            table = self.oracle_config['table']
            
            # Process each row
            inserted = 0
            updated = 0
            
            for _, row in df.iterrows():
                try:
                    # Check if license exists
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM "{schema}".{table}
                        WHERE LIC_ID = :lic_id
                    """, lic_id=row.get('LIC_ID'))
                    
                    exists = cursor.fetchone()[0] > 0
                    
                    if exists:
                        # Update existing record
                        cursor.execute(f"""
                            UPDATE "{schema}".{table}
                            SET LIC_NAME = :lic_name,
                                LIC_STATE = :lic_state,
                                LIC_TYPE = :lic_type,
                                LIC_NO = :lic_no,
                                ASCEM_NO = :ascem_no,
                                FIRST_ISSUE_DATE = :first_issue_date,
                                EXPIRATION_DATE = :expiration_date,
                                LIC_NOTIFY_NAMES = :lic_notify_names,
                                UPDATED_AT = SYSDATE
                            WHERE LIC_ID = :lic_id
                        """, {
                            'lic_id': row.get('LIC_ID'),
                            'lic_name': row.get('LIC_NAME'),
                            'lic_state': row.get('LIC_STATE'),
                            'lic_type': row.get('LIC_TYPE'),
                            'lic_no': row.get('LIC_NO'),
                            'ascem_no': row.get('ASCEM_NO'),
                            'first_issue_date': pd.to_datetime(row.get('FIRST_ISSUE_DATE')) if pd.notna(row.get('FIRST_ISSUE_DATE')) else None,
                            'expiration_date': pd.to_datetime(row.get('EXPIRATION_DATE')) if pd.notna(row.get('EXPIRATION_DATE')) else None,
                            'lic_notify_names': row.get('LIC_NOTIFY_NAMES')
                        })
                        updated += 1
                    else:
                        # Insert new record
                        cursor.execute(f"""
                            INSERT INTO "{schema}".{table} (
                                LIC_ID, LIC_NAME, LIC_STATE, LIC_TYPE, LIC_NO,
                                ASCEM_NO, FIRST_ISSUE_DATE, EXPIRATION_DATE,
                                LIC_NOTIFY_NAMES, CREATED_AT, UPDATED_AT
                            ) VALUES (
                                :lic_id, :lic_name, :lic_state, :lic_type, :lic_no,
                                :ascem_no, :first_issue_date, :expiration_date,
                                :lic_notify_names, SYSDATE, SYSDATE
                            )
                        """, {
                            'lic_id': row.get('LIC_ID'),
                            'lic_name': row.get('LIC_NAME'),
                            'lic_state': row.get('LIC_STATE'),
                            'lic_type': row.get('LIC_TYPE'),
                            'lic_no': row.get('LIC_NO'),
                            'ascem_no': row.get('ASCEM_NO'),
                            'first_issue_date': pd.to_datetime(row.get('FIRST_ISSUE_DATE')) if pd.notna(row.get('FIRST_ISSUE_DATE')) else None,
                            'expiration_date': pd.to_datetime(row.get('EXPIRATION_DATE')) if pd.notna(row.get('EXPIRATION_DATE')) else None,
                            'lic_notify_names': row.get('LIC_NOTIFY_NAMES')
                        })
                        inserted += 1
                        
                except Exception as e:
                    logger.error(f"Error processing row {row.get('LIC_ID')}: {e}")
                    continue
            
            connection.commit()
            cursor.close()
            connection.close()
            
            logger.info(f"Upload complete: {inserted} inserted, {updated} updated")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading Excel data: {e}")
            return False
    
    def get_licenses_needing_reminders(self) -> List[Dict[str, Any]]:
        """Get licenses that need reminders today from Oracle view"""
        try:
            connection = self.get_oracle_connection()
            cursor = connection.cursor()
            schema = self.oracle_config['schema']
            
            # Query the view that filters licenses needing reminders
            cursor.execute(f"""
                SELECT id, lic_name, lic_type, lic_state, expiration_date,
                       lic_notify_names, days_until_expiration, reminder_type
                FROM "{schema}".LICENSES_NEEDING_REMINDERS
            """)
            
            columns = [col[0].lower() for col in cursor.description]
            licenses = []
            
            for row in cursor:
                license_dict = dict(zip(columns, row))
                licenses.append(license_dict)
            
            cursor.close()
            connection.close()
            
            logger.info(f"Found {len(licenses)} licenses needing reminders")
            return licenses
            
        except Exception as e:
            logger.error(f"Error fetching licenses needing reminders: {e}")
            return []
    
    def get_upcoming_expirations(self, days: int = 90) -> List[Dict[str, Any]]:
        """Get licenses expiring in the next N days"""
        try:
            connection = self.get_oracle_connection()
            cursor = connection.cursor()
            schema = self.oracle_config['schema']
            
            cursor.execute(f"""
                SELECT * FROM "{schema}".UPCOMING_EXPIRATIONS
                WHERE days_until_expiration <= :days
                ORDER BY expiration_date
            """, days=days)
            
            columns = [col[0].lower() for col in cursor.description]
            licenses = []
            
            for row in cursor:
                license_dict = dict(zip(columns, row))
                licenses.append(license_dict)
            
            cursor.close()
            connection.close()
            
            return licenses
            
        except Exception as e:
            logger.error(f"Error fetching upcoming expirations: {e}")
            return []
    
    def send_reminder_email(self, license_data: Dict[str, Any]) -> bool:
        """Send reminder email for a license"""
        try:
            # Parse email addresses
            email_list = []
            if license_data.get('lic_notify_names'):
                emails = str(license_data['lic_notify_names']).split(',')
                email_list = [email.strip() for email in emails if email.strip()]
            
            if not email_list:
                logger.warning(f"No email addresses for license {license_data.get('id')}")
                return False
            
            # Prepare email content
            subject = self.get_email_subject(license_data)
            body = self.get_email_body(license_data)
            
            # Send email
            success = self.send_email(email_list, subject, body)
            
            if success:
                # Record the sent reminder in database
                self.record_email_reminder(license_data, email_list, subject, body)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending reminder email: {e}")
            return False
    
    def get_email_subject(self, license_data: Dict[str, Any]) -> str:
        """Generate email subject based on reminder type"""
        days = license_data.get('days_until_expiration', 0)
        lic_name = license_data.get('lic_name', 'License')
        lic_type = license_data.get('lic_type', 'License')
        
        if days < 0:
            return f"⚠️ OVERDUE: {lic_name} - {lic_type} has expired"
        elif days == 1:
            return f"🚨 URGENT: {lic_name} - {lic_type} expires TOMORROW"
        elif days <= 7:
            return f"⚠️ ALERT: {lic_name} - {lic_type} expires in {days} days"
        elif days <= 15:
            return f"📅 REMINDER: {lic_name} - {lic_type} expires in {days} days"
        else:
            return f"📢 Notice: {lic_name} - {lic_type} expires in {days} days"
    
    def get_email_body(self, license_data: Dict[str, Any]) -> str:
        """Generate email body HTML"""
        days = license_data.get('days_until_expiration', 0)
        expiration_date = license_data.get('expiration_date')
        
        if isinstance(expiration_date, datetime):
            exp_date_str = expiration_date.strftime('%B %d, %Y')
        else:
            exp_date_str = str(expiration_date)
        
        urgency_color = '#dc3545' if days <= 7 else '#ffc107' if days <= 15 else '#17a2b8'
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {urgency_color}; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 20px; margin-top: 20px; }}
                .license-info {{ background-color: white; padding: 15px; border-left: 4px solid {urgency_color}; margin: 15px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                .button {{ background-color: {urgency_color}; color: white; padding: 10px 20px; text-decoration: none; display: inline-block; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>License Expiration {"OVERDUE" if days < 0 else "Reminder"}</h1>
                </div>
                
                <div class="content">
                    <p>Dear License Holder,</p>
                    
                    {"<p><strong>⚠️ This license has EXPIRED and requires immediate attention!</strong></p>" if days < 0 else f"<p>This is a reminder that the following license will expire in <strong>{days} day{'s' if days != 1 else ''}</strong>:</p>"}
                    
                    <div class="license-info">
                        <strong>License Holder:</strong> {license_data.get('lic_name', 'N/A')}<br>
                        <strong>License Type:</strong> {license_data.get('lic_type', 'N/A')}<br>
                        <strong>State:</strong> {license_data.get('lic_state', 'N/A')}<br>
                        <strong>License Number:</strong> {license_data.get('lic_no', 'N/A')}<br>
                        <strong>Expiration Date:</strong> <span style="color: {urgency_color}; font-weight: bold;">{exp_date_str}</span>
                    </div>
                    
                    <p><strong>Action Required:</strong></p>
                    <ul>
                        <li>Review the license details above</li>
                        <li>{"Renew this license IMMEDIATELY" if days < 0 else "Begin the renewal process if not already started"}</li>
                        <li>Contact the appropriate licensing authority</li>
                        <li>Update our records once renewed</li>
                    </ul>
                    
                    <p>If you have already renewed this license, please update our records or contact support.</p>
                </div>
                
                <div class="footer">
                    <p>This is an automated reminder from {self.company_info['name']}<br>
                    For assistance, contact: {self.company_info['support_email']}<br>
                    <a href="{self.company_info['website']}">{self.company_info['website']}</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_body
    
    def send_email(self, recipients: List[str], subject: str, body: str) -> bool:
        """Send email using SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.email_config['from_name']} <{self.email_config['from_email']}>"
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['username'], self.email_config['password'])
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {', '.join(recipients)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def record_email_reminder(self, license_data: Dict[str, Any], recipients: List[str], 
                             subject: str, body: str):
        """Record sent email reminder in Oracle database"""
        try:
            connection = self.get_oracle_connection()
            cursor = connection.cursor()
            schema = self.oracle_config['schema']
            
            cursor.execute(f"""
                INSERT INTO "{schema}".EMAIL_REMINDERS (
                    LICENSE_ID, REMINDER_TYPE, EMAIL_TO, 
                    EMAIL_SUBJECT, EMAIL_BODY, STATUS
                ) VALUES (
                    :license_id, :reminder_type, :email_to,
                    :email_subject, :email_body, :status
                )
            """, {
                'license_id': license_data.get('id'),
                'reminder_type': license_data.get('reminder_type'),
                'email_to': ', '.join(recipients),
                'email_subject': subject,
                'email_body': body,
                'status': 'sent'
            })
            
            connection.commit()
            cursor.close()
            connection.close()
            
            logger.info(f"Reminder recorded for license {license_data.get('id')}")
            
        except Exception as e:
            logger.error(f"Error recording email reminder: {e}")
    
    def check_and_send_reminders(self):
        """Check for licenses needing reminders and send emails"""
        logger.info("Starting reminder check...")
        
        licenses = self.get_licenses_needing_reminders()
        
        if not licenses:
            logger.info("No licenses need reminders today")
            return
        
        sent_count = 0
        failed_count = 0
        
        for license_data in licenses:
            if self.send_reminder_email(license_data):
                sent_count += 1
            else:
                failed_count += 1
        
        logger.info(f"Reminder check complete: {sent_count} sent, {failed_count} failed")
    
    def run_scheduler(self):
        """Run the scheduler for daily checks"""
        logger.info("Starting License Reminder Scheduler (Oracle)")
        logger.info("Scheduled to run daily at 9:00 AM")
        
        # Schedule daily check at 9:00 AM
        schedule.every().day.at("09:00").do(self.check_and_send_reminders)
        
        # Run initial check
        self.check_and_send_reminders()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics from Oracle"""
        try:
            connection = self.get_oracle_connection()
            cursor = connection.cursor()
            schema = self.oracle_config['schema']
            
            stats = {}
            
            # Total licenses
            cursor.execute(f'SELECT COUNT(*) FROM "{schema}".LICENSES')
            stats['total_licenses'] = cursor.fetchone()[0]
            
            # Licenses with emails
            cursor.execute(f"""
                SELECT COUNT(*) FROM "{schema}".LICENSES 
                WHERE LIC_NOTIFY_NAMES IS NOT NULL
            """)
            stats['licenses_with_emails'] = cursor.fetchone()[0]
            
            # Upcoming expirations
            cursor.execute(f'SELECT COUNT(*) FROM "{schema}".UPCOMING_EXPIRATIONS')
            stats['upcoming_expirations'] = cursor.fetchone()[0]
            
            # Overdue licenses
            cursor.execute(f'SELECT COUNT(*) FROM "{schema}".OVERDUE_LICENSES')
            stats['overdue_licenses'] = cursor.fetchone()[0]
            
            # Reminders sent today
            cursor.execute(f"""
                SELECT COUNT(*) FROM "{schema}".EMAIL_REMINDERS
                WHERE TRUNC(SENT_DATE) = TRUNC(SYSDATE)
            """)
            stats['reminders_sent_today'] = cursor.fetchone()[0]
            
            # Total reminders sent
            cursor.execute(f'SELECT COUNT(*) FROM "{schema}".EMAIL_REMINDERS')
            stats['total_reminders_sent'] = cursor.fetchone()[0]
            
            cursor.close()
            connection.close()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python license_reminder_oracle.py [upload|check|schedule|stats]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    try:
        system = LicenseReminderOracleSystem()
        
        if command == 'upload':
            print("Uploading Excel data to Oracle...")
            if system.upload_excel_data():
                print("✅ Upload successful!")
            else:
                print("❌ Upload failed. Check logs for details.")
        
        elif command == 'check':
            print("Checking for licenses needing reminders...")
            system.check_and_send_reminders()
            print("✅ Reminder check complete!")
        
        elif command == 'schedule':
            print("Starting scheduler...")
            system.run_scheduler()
        
        elif command == 'stats':
            print("\nLicense Reminder System Statistics (Oracle)")
            print("=" * 50)
            stats = system.get_statistics()
            for key, value in stats.items():
                print(f"{key.replace('_', ' ').title()}: {value}")
            print("=" * 50)
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: upload, check, schedule, stats")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()