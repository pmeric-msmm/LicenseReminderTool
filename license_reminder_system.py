#!/usr/bin/env python3
"""
License Reminder System
Uploads Excel data to Supabase and sends automated email reminders
30, 15, and 10 days before license expiration
"""

import os
import sys
import pandas as pd
import smtplib
import schedule
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import List, Dict, Optional
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('license_reminders.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class LicenseReminderSystem:
    def __init__(self):
        """Initialize the License Reminder System"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_username = os.getenv('EMAIL_USERNAME')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL')
        self.from_name = os.getenv('FROM_NAME', 'License Reminder System')
        self.excel_file_path = os.getenv('EXCEL_FILE_PATH', 'licenses.xlsx')
        self.company_name = os.getenv('COMPANY_NAME', 'MSMM Engineering')
        self.company_website = os.getenv('COMPANY_WEBSITE', 'https://www.msmmeng.com')
        self.support_email = os.getenv('SUPPORT_EMAIL', 'support@msmmeng.com')
        
        # Validate required environment variables
        if not all([self.supabase_url, self.supabase_key, self.email_username, 
                   self.email_password, self.from_email]):
            raise ValueError("Missing required environment variables. Check your .env file.")
        
        # Initialize Supabase client
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        logger.info("License Reminder System initialized successfully")

    def upload_excel_to_supabase(self) -> bool:
        """Upload Excel data to Supabase"""
        try:
            logger.info(f"Reading Excel file: {self.excel_file_path}")
            df = pd.read_excel(self.excel_file_path)
            
            # Clean and prepare data
            df = df.dropna(subset=['LIC_ID'])  # Remove rows without license ID (LIC_ID used for data validation only)
            
            # Convert dates to string format for Supabase
            date_columns = ['FIRST_ISSUE_DATE', 'EXPIRATION_DATE']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    df[col] = df[col].dt.strftime('%Y-%m-%d')
                    df[col] = df[col].replace('NaT', None)
            
            # Convert column names to lowercase for database
            df.columns = df.columns.str.lower()
            
            # Handle NaN values more thoroughly
            # Replace all NaN, inf, -inf with None
            df = df.replace([float('inf'), float('-inf')], None)
            df = df.where(pd.notna(df), None)
            
            # Convert DataFrame to list of dictionaries
            records = df.to_dict('records')
            
            # Additional cleaning for each record
            cleaned_records = []
            for record in records:
                cleaned_record = {}
                for key, value in record.items():
                    # Handle different types of invalid values
                    if pd.isna(value) or value == 'nan' or str(value).lower() == 'nan':
                        cleaned_record[key] = None
                    elif isinstance(value, float) and (value != value):  # Check for NaN
                        cleaned_record[key] = None
                    else:
                        # Special handling for numeric columns
                        if key in ['lic_id', 'ascem_no'] and value is not None:
                            try:
                                # Convert to int if it's a valid number
                                cleaned_record[key] = int(float(value))
                            except (ValueError, TypeError):
                                cleaned_record[key] = None
                        else:
                            cleaned_record[key] = value
                cleaned_records.append(cleaned_record)
            
            logger.info(f"Uploading {len(cleaned_records)} records to Supabase")
            
            # Clear existing data and insert new data
            # First, get existing records to avoid duplicates
            existing_result = self.supabase.table('licenses').select('lic_id').execute()
            existing_lic_ids = {row['lic_id'] for row in existing_result.data}
            
            # Filter out existing records
            new_records = [record for record in cleaned_records if record['lic_id'] not in existing_lic_ids]
            
            if new_records:
                result = self.supabase.table('licenses').insert(new_records).execute()
                logger.info(f"Successfully uploaded {len(new_records)} new records")
            else:
                logger.info("No new records to upload")
                
            # Update existing records if needed
            existing_records = [record for record in cleaned_records if record['lic_id'] in existing_lic_ids]
            for record in existing_records:
                self.supabase.table('licenses').update(record).eq('lic_id', record['lic_id']).execute()
            
            if existing_records:
                logger.info(f"Updated {len(existing_records)} existing records")
            
            return True
            
        except Exception as e:
            logger.error(f"Error uploading Excel data: {str(e)}")
            return False

    def get_licenses_needing_reminders(self) -> List[Dict]:
        """Get licenses that need reminders (30, 15, 10 days before expiration)"""
        try:
            # Use the view we created in the schema
            result = self.supabase.table('licenses_needing_reminders').select('*').execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching licenses needing reminders: {str(e)}")
            return []

    def create_email_content(self, license_data: Dict, reminder_type: str) -> tuple:
        """Create email subject and body for reminder"""
        
        # Handle different reminder types
        if reminder_type == 'overdue_daily':
            days_overdue = license_data.get('days_overdue', 'several')
            subject = f"🚨 OVERDUE LICENSE - {license_data['lic_name']} (Expired {days_overdue} days ago)"
            urgency = "URGENT: "
            time_message = f"expired {days_overdue} days ago"
            action_message = "Your license has expired! Please renew immediately to avoid legal and professional complications."
        else:
            days = reminder_type.split('_')[0]
            subject = f"License Expiration Reminder - {license_data['lic_name']} ({days} days remaining)"
            urgency = ""
            time_message = f"is set to expire in {days} days"
            
            if days == '1':
                action_message = "⚠️ CRITICAL: Your license expires tomorrow! Please renew immediately."
            elif days == '7':
                action_message = "⚠️ URGENT: Your license expires in one week. Please begin renewal process immediately."
            elif days == '15':
                action_message = "Please begin your license renewal process soon to ensure continuity."
            elif days == '30':
                action_message = "Please start planning your license renewal to avoid any last-minute issues."
            elif days == '60':
                action_message = "This is an early reminder to help you plan your license renewal process."
            else:
                action_message = "Please take the necessary steps to renew your license before the expiration date."
        
        body = f"""
Dear {license_data['lic_name']},

{urgency}This is an automated reminder that your {license_data.get('lic_type', 'license')} license in {license_data.get('lic_state', 'N/A')} {time_message}.

License Details:
- License Type: {license_data.get('lic_type', 'N/A')}
- License Number: {license_data.get('lic_no', 'N/A')}
- State: {license_data.get('lic_state', 'N/A')}
- Expiration Date: {license_data.get('expiration_date', 'N/A')}

{action_message}

{self._get_renewal_guidance(reminder_type)}

If you have already renewed this license, please disregard this message.

For any questions or concerns, please contact us at {self.support_email}.

Best regards,
{self.from_name}
{self.company_name}
{self.company_website}

---
This is an automated message. Please do not reply to this email.
        """.strip()
        
        return subject, body

    def _get_renewal_guidance(self, reminder_type: str) -> str:
        """Get renewal guidance based on reminder type"""
        if reminder_type == 'overdue_daily':
            return """
IMMEDIATE ACTION REQUIRED:
- Contact the licensing authority immediately
- Check if late renewal is possible and what penalties apply
- Verify if you can continue professional activities during renewal process
- Consider temporary licensing options if available
"""
        elif reminder_type == '1_day':
            return """
IMMEDIATE ACTION REQUIRED:
- Submit renewal application TODAY if not already done
- Ensure all required documentation is complete
- Contact licensing authority if you need assistance
- Prepare for potential service interruption if renewal is not completed in time
"""
        elif reminder_type == '7_days':
            return """
URGENT ACTION REQUIRED:
- Submit renewal application this week
- Gather all required documentation
- Pay any required fees
- Schedule any required continuing education or examinations
"""
        elif reminder_type in ['15_days', '30_days']:
            return """
RECOMMENDED ACTIONS:
- Review renewal requirements and deadlines
- Gather necessary documentation and certifications
- Complete any required continuing education
- Prepare renewal fees and submit application
"""
        elif reminder_type == '60_days':
            return """
EARLY PLANNING REMINDER:
- Review renewal requirements for your license
- Check if continuing education credits are needed
- Verify current contact information with licensing authority
- Plan ahead to avoid last-minute complications
"""
        else:
            return """
RECOMMENDED ACTIONS:
- Review renewal requirements and deadlines
- Begin gathering necessary documentation
- Plan for any required fees or continuing education
"""

    def send_email(self, to_emails: List[str], subject: str, body: str) -> bool:
        """Send email reminder"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # Add body to email
            msg.attach(MIMEText(body, 'plain'))
            
            # Setup SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_username, self.email_password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(self.from_email, to_emails, text)
            server.quit()
            
            logger.info(f"Email sent successfully to: {', '.join(to_emails)}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {', '.join(to_emails)}: {str(e)}")
            return False

    def parse_email_addresses(self, email_string: str) -> List[str]:
        """Parse email addresses from string (comma-separated)"""
        if not email_string or pd.isna(email_string):
            return []
        
        emails = [email.strip() for email in str(email_string).split(',')]
        # Basic email validation
        valid_emails = [email for email in emails if '@' in email and '.' in email]
        return valid_emails

    def record_reminder_sent(self, license_id: int, reminder_type: str, 
                           email_addresses: List[str], subject: str, body: str, 
                           status: str = 'sent') -> bool:
        """Record that a reminder was sent"""
        try:
            reminder_data = {
                'license_id': license_id,
                'reminder_type': reminder_type,
                'email_addresses': ', '.join(email_addresses),
                'email_subject': subject,
                'email_body': body,
                'status': status
            }
            
            result = self.supabase.table('email_reminders').insert(reminder_data).execute()
            return True
            
        except Exception as e:
            logger.error(f"Error recording reminder: {str(e)}")
            return False

    def process_reminders(self):
        """Process and send all pending reminders"""
        logger.info("Starting reminder processing...")
        
        # Get licenses needing reminders
        licenses = self.get_licenses_needing_reminders()
        
        if not licenses:
            logger.info("No licenses need reminders today")
            return
        
        logger.info(f"Found {len(licenses)} licenses needing reminders")
        
        for license_data in licenses:
            try:
                # Parse email addresses
                email_addresses = self.parse_email_addresses(license_data.get('lic_notify_names'))
                
                if not email_addresses:
                    logger.warning(f"No valid email addresses for license {license_data['lic_id']}")
                    continue
                
                # Create email content
                subject, body = self.create_email_content(license_data, license_data['reminder_type'])
                
                # Send email
                email_sent = self.send_email(email_addresses, subject, body)
                
                # Record the reminder attempt
                self.record_reminder_sent(
                    license_data['id'],
                    license_data['reminder_type'],
                    email_addresses,
                    subject,
                    body,
                    'sent' if email_sent else 'failed'
                )
                
                if email_sent:
                    logger.info(f"Reminder sent for {license_data['lic_name']} - {license_data['reminder_type']}")
                else:
                    logger.error(f"Failed to send reminder for {license_data['lic_name']}")
                
            except Exception as e:
                logger.error(f"Error processing reminder for license {license_data.get('lic_id')}: {str(e)}")
        
        logger.info("Reminder processing completed")

    def run_daily_check(self):
        """Run daily check for reminders"""
        logger.info("Running daily reminder check...")
        self.process_reminders()

    def start_scheduler(self):
        """Start the reminder scheduler"""
        logger.info("Starting license reminder scheduler...")
        
        # Schedule daily checks at 9:00 AM
        schedule.every().day.at("09:00").do(self.run_daily_check)
        
        logger.info("Scheduler started. Daily reminders will be sent at 9:00 AM")
        logger.info("Press Ctrl+C to stop the scheduler")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python license_reminder_system.py upload    - Upload Excel data to Supabase")
        print("  python license_reminder_system.py check     - Run reminder check once")
        print("  python license_reminder_system.py schedule  - Start daily scheduler")
        return
    
    command = sys.argv[1].lower()
    
    try:
        system = LicenseReminderSystem()
        
        if command == 'upload':
            logger.info("Uploading Excel data to Supabase...")
            success = system.upload_excel_to_supabase()
            if success:
                logger.info("Excel data uploaded successfully!")
            else:
                logger.error("Failed to upload Excel data")
                
        elif command == 'check':
            logger.info("Running reminder check...")
            system.process_reminders()
            
        elif command == 'schedule':
            logger.info("Starting scheduler...")
            system.start_scheduler()
            
        else:
            print(f"Unknown command: {command}")
            print("Use 'upload', 'check', or 'schedule'")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 