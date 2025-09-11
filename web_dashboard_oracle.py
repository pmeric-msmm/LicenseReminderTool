"""
Web Dashboard for License Reminder System - Oracle Database Version with CRUD
Flask-based web interface for viewing and managing license data
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from dotenv import load_dotenv
import oracledb
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-change-this')

@app.context_processor
def inject_current_date():
    """Make current date available to all templates"""
    return dict(current_date=datetime.now())

# Oracle configuration
ORACLE_CONFIG = {
    'host': os.getenv('ORACLE_HOST'),
    'port': int(os.getenv('ORACLE_PORT', 1521)),
    'service': os.getenv('ORACLE_SERVICE_NAME'),
    'user': os.getenv('ORACLE_USER', 'SYS'),
    'password': os.getenv('ORACLE_PASSWORD'),
    'schema': os.getenv('ORACLE_SCHEMA')
}

# Company information
COMPANY_INFO = {
    'name': os.getenv('COMPANY_NAME', 'MSMM Engineering'),
    'website': os.getenv('COMPANY_WEBSITE', 'https://www.msmmeng.com'),
    'support_email': os.getenv('SUPPORT_EMAIL', 'support@msmmeng.com')
}


def get_oracle_connection():
    """Create and return an Oracle database connection"""
    try:
        dsn = oracledb.makedsn(
            ORACLE_CONFIG['host'],
            ORACLE_CONFIG['port'],
            service_name=ORACLE_CONFIG['service']
        )
        
        connection = oracledb.connect(
            user=ORACLE_CONFIG['user'],
            password=ORACLE_CONFIG['password'],
            dsn=dsn,
            mode=oracledb.AUTH_MODE_SYSDBA
        )
        
        return connection
    except oracledb.Error as e:
        logger.error(f"Oracle connection error: {e}")
        raise


def query_oracle(query, params=None):
    """Execute a query and return results as list of dictionaries"""
    try:
        connection = get_oracle_connection()
        cursor = connection.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Check if this is a SELECT query
        if query.strip().upper().startswith('SELECT'):
            columns = [col[0].lower() for col in cursor.description]
            results = []
            
            for row in cursor:
                result_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # Convert Oracle datetime to Python datetime string for JSON serialization
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    # Handle CLOB fields
                    elif hasattr(value, 'read'):
                        value = value.read() if value else None
                    result_dict[col] = value
                results.append(result_dict)
            
            cursor.close()
            connection.close()
            return results
        else:
            # For INSERT, UPDATE, DELETE
            connection.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            connection.close()
            return affected_rows
        
    except Exception as e:
        logger.error(f"Query error: {e}")
        if 'connection' in locals():
            connection.rollback()
            connection.close()
        raise


@app.route('/')
def dashboard():
    """Main dashboard page"""
    try:
        schema = ORACLE_CONFIG['schema']
        
        # Get filter parameters with defaults
        filter_upcoming = int(request.args.get('upcoming_days', 60))
        filter_critical = int(request.args.get('critical_days', 7))  # Default to 7 days for critical
        filter_warning = int(request.args.get('warning_days', 30))
        
        # Get statistics
        stats = {
            'total_licenses': 0,
            'expiring_soon': 0,
            'overdue': 0,
            'past_due_count': 0,
            'upcoming_expirations': 0,
            'reminders_sent_today': 0,
            'critical_count': 0,
            'warning_count': 0,
            'normal_count': 0
        }
        
        # Total licenses
        result = query_oracle(f'SELECT COUNT(*) as count FROM "{schema}".LICENSES')
        if result:
            stats['total_licenses'] = result[0]['count']
        
        # Expiring soon / Upcoming expirations (using filter parameter)
        result = query_oracle(f"""
            SELECT COUNT(*) as count FROM "{schema}".LICENSES
            WHERE EXPIRATION_DATE IS NOT NULL
            AND EXPIRATION_DATE >= SYSDATE
            AND EXPIRATION_DATE <= SYSDATE + :days
        """, {'days': filter_upcoming})
        if result:
            stats['expiring_soon'] = result[0]['count']
            stats['upcoming_expirations'] = result[0]['count']
        
        # Critical (using filter parameter)
        result = query_oracle(f"""
            SELECT COUNT(*) as count FROM "{schema}".LICENSES
            WHERE EXPIRATION_DATE >= SYSDATE
            AND EXPIRATION_DATE <= SYSDATE + :days
        """, {'days': filter_critical})
        if result:
            stats['critical_count'] = result[0]['count']
        
        # Warning (between critical and warning days)
        result = query_oracle(f"""
            SELECT COUNT(*) as count FROM "{schema}".LICENSES
            WHERE EXPIRATION_DATE > SYSDATE + :critical
            AND EXPIRATION_DATE <= SYSDATE + :warning
        """, {'critical': filter_critical, 'warning': filter_warning})
        if result:
            stats['warning_count'] = result[0]['count']
        
        # Normal (31-35 days by default)
        result = query_oracle(f"""
            SELECT COUNT(*) as count FROM "{schema}".LICENSES
            WHERE EXPIRATION_DATE > SYSDATE + :warning
            AND EXPIRATION_DATE <= SYSDATE + :upcoming
        """, {'warning': filter_warning, 'upcoming': filter_upcoming})
        if result:
            stats['normal_count'] = result[0]['count']
        
        # Overdue / Past Due
        result = query_oracle(f"""
            SELECT COUNT(*) as count FROM "{schema}".LICENSES
            WHERE EXPIRATION_DATE < SYSDATE
            AND EXPIRATION_DATE IS NOT NULL
        """)
        if result:
            stats['overdue'] = result[0]['count']
            stats['past_due_count'] = result[0]['count']
        
        # Reminders sent today
        result = query_oracle(f"""
            SELECT COUNT(*) as count FROM "{schema}".EMAIL_REMINDERS
            WHERE TRUNC(SENT_DATE) = TRUNC(SYSDATE)
        """)
        if result:
            stats['reminders_sent_today'] = result[0]['count']
        
        # Get past due licenses (no limit for dashboard display)
        past_due = query_oracle(f"""
            SELECT 
                LIC_ID as id,
                LIC_NAME as lic_name,
                LIC_TYPE as lic_type,
                LIC_STATE as lic_state,
                LIC_NO as lic_no,
                EXPIRATION_DATE as expiration_date,
                TRUNC(SYSDATE) - TRUNC(EXPIRATION_DATE) as days_overdue
            FROM "{schema}".LICENSES
            WHERE EXPIRATION_DATE < SYSDATE
            AND EXPIRATION_DATE IS NOT NULL
            ORDER BY EXPIRATION_DATE DESC
        """)
        
        # Get critical licenses (0-7 days by default)
        critical = query_oracle(f"""
            SELECT 
                LIC_ID as id,
                LIC_NAME as lic_name,
                LIC_TYPE as lic_type,
                LIC_STATE as lic_state,
                LIC_NO as lic_no,
                EXPIRATION_DATE as expiration_date,
                TRUNC(EXPIRATION_DATE) - TRUNC(SYSDATE) as days_until_expiration
            FROM "{schema}".LICENSES
            WHERE EXPIRATION_DATE >= SYSDATE
            AND EXPIRATION_DATE <= SYSDATE + :days
            ORDER BY EXPIRATION_DATE
        """, {'days': filter_critical})
        
        # Get warning licenses (8-30 days by default)
        warning = query_oracle(f"""
            SELECT 
                LIC_ID as id,
                LIC_NAME as lic_name,
                LIC_TYPE as lic_type,
                LIC_STATE as lic_state,
                LIC_NO as lic_no,
                EXPIRATION_DATE as expiration_date,
                TRUNC(EXPIRATION_DATE) - TRUNC(SYSDATE) as days_until_expiration
            FROM "{schema}".LICENSES
            WHERE EXPIRATION_DATE > SYSDATE + :critical
            AND EXPIRATION_DATE <= SYSDATE + :warning
            ORDER BY EXPIRATION_DATE
        """, {'critical': filter_critical, 'warning': filter_warning})
        
        # Get normal upcoming licenses (31-35 days by default)
        normal = query_oracle(f"""
            SELECT 
                LIC_ID as id,
                LIC_NAME as lic_name,
                LIC_TYPE as lic_type,
                LIC_STATE as lic_state,
                LIC_NO as lic_no,
                EXPIRATION_DATE as expiration_date,
                TRUNC(EXPIRATION_DATE) - TRUNC(SYSDATE) as days_until_expiration
            FROM "{schema}".LICENSES
            WHERE EXPIRATION_DATE > SYSDATE + :warning
            AND EXPIRATION_DATE <= SYSDATE + :upcoming
            ORDER BY EXPIRATION_DATE
        """, {'warning': filter_warning, 'upcoming': filter_upcoming})
        
        # Get ALL upcoming licenses (0-35 days) in one list
        all_upcoming = query_oracle(f"""
            SELECT 
                LIC_ID as id,
                LIC_NAME as lic_name,
                LIC_TYPE as lic_type,
                LIC_STATE as lic_state,
                LIC_NO as lic_no,
                EXPIRATION_DATE as expiration_date,
                TRUNC(EXPIRATION_DATE) - TRUNC(SYSDATE) as days_until_expiration
            FROM "{schema}".LICENSES
            WHERE EXPIRATION_DATE >= SYSDATE
            AND EXPIRATION_DATE <= SYSDATE + :upcoming
            ORDER BY EXPIRATION_DATE
        """, {'upcoming': filter_upcoming})
        
        
        # Get recent reminders
        recent_reminders = query_oracle(f"""
            SELECT * FROM (
                SELECT 
                    er.ID,
                    er.LICENSE_ID,
                    l.LIC_NAME,
                    er.REMINDER_TYPE,
                    er.SENT_DATE,
                    er.EMAIL_TO
                FROM "{schema}".EMAIL_REMINDERS er
                LEFT JOIN "{schema}".LICENSES l ON er.LICENSE_ID = l.LIC_ID
                ORDER BY er.SENT_DATE DESC
            ) WHERE ROWNUM <= 5
        """)
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             past_due=past_due,
                             critical=critical,
                             warning=warning,
                             normal=normal,
                             all_upcoming=all_upcoming,
                             recent_reminders=recent_reminders,
                             filter_upcoming=filter_upcoming,
                             filter_critical=filter_critical,
                             filter_warning=filter_warning,
                             company_info=COMPANY_INFO)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        return render_template('dashboard.html', 
                             stats={'total_licenses': 0, 'expiring_soon': 0, 'overdue': 0, 
                                   'past_due_count': 0, 'upcoming_expirations': 0,
                                   'reminders_sent_today': 0, 'critical_count': 0, 
                                   'warning_count': 0, 'normal_count': 0},
                             past_due=[],
                             critical=[],
                             warning=[],
                             normal=[],
                             all_upcoming=[],
                             recent_reminders=[],
                             filter_upcoming=60,
                             filter_critical=7,
                             filter_warning=30,
                             company_info=COMPANY_INFO)


@app.route('/licenses')
def licenses():
    """View all licenses with filtering"""
    try:
        schema = ORACLE_CONFIG['schema']
        
        # Get filter parameters
        filter_type = request.args.get('filter', 'all')
        search_query = request.args.get('search', '')
        
        # Get dynamic filter parameters from URL
        upcoming_days = int(request.args.get('upcoming_days', 60))
        critical_days = int(request.args.get('critical_days', 7))
        warning_days = int(request.args.get('warning_days', 30))
        
        # Build base query
        base_query = f"""
            SELECT 
                LIC_ID as id,
                LIC_NAME as lic_name,
                LIC_STATE as lic_state,
                LIC_TYPE as lic_type,
                LIC_NO as lic_no,
                ASCEM_NO as ascem_no,
                FIRST_ISSUE_DATE as first_issue_date,
                EXPIRATION_DATE as expiration_date,
                LIC_NOTIFY_NAMES as lic_notify_names,
                LIC_COMMENTS as lic_comments,
                TRUNC(EXPIRATION_DATE) - TRUNC(SYSDATE) as days_until_expiration
            FROM "{schema}".LICENSES
        """
        
        where_conditions = []
        
        # Apply filters based on filter_type
        if filter_type == 'expiring':
            where_conditions.append(f"""
                EXPIRATION_DATE IS NOT NULL 
                AND EXPIRATION_DATE >= SYSDATE 
                AND EXPIRATION_DATE <= SYSDATE + {upcoming_days}
            """)
        elif filter_type == 'critical':
            where_conditions.append(f"""
                EXPIRATION_DATE IS NOT NULL 
                AND EXPIRATION_DATE >= SYSDATE 
                AND EXPIRATION_DATE <= SYSDATE + {critical_days}
            """)
        elif filter_type == 'warning':
            where_conditions.append(f"""
                EXPIRATION_DATE IS NOT NULL 
                AND EXPIRATION_DATE > SYSDATE + {critical_days}
                AND EXPIRATION_DATE <= SYSDATE + {warning_days}
            """)
        elif filter_type == 'past_due' or filter_type == 'overdue':
            where_conditions.append("EXPIRATION_DATE IS NOT NULL AND EXPIRATION_DATE < SYSDATE")
        elif filter_type == 'no-email':
            where_conditions.append("(LIC_NOTIFY_NAMES IS NULL OR TRIM(LIC_NOTIFY_NAMES) IS NULL)")
        
        # Apply search
        if search_query:
            search_condition = f"""
                (UPPER(LIC_NAME) LIKE UPPER('%{search_query}%')
                OR UPPER(LIC_TYPE) LIKE UPPER('%{search_query}%')
                OR UPPER(LIC_STATE) LIKE UPPER('%{search_query}%')
                OR UPPER(LIC_NO) LIKE UPPER('%{search_query}%'))
            """
            where_conditions.append(search_condition)
        
        if where_conditions:
            base_query += " WHERE " + " AND ".join(where_conditions)
        
        base_query += " ORDER BY EXPIRATION_DATE NULLS LAST, LIC_NAME"
        
        all_licenses = query_oracle(base_query)
        
        # Process licenses for display
        processed_licenses = []
        for license in all_licenses:
            license_copy = license.copy()
            
            # Calculate status
            if license.get('expiration_date'):
                days_until = license.get('days_until_expiration')
                
                if days_until is not None:
                    if days_until < 0:
                        license_copy['status'] = 'Overdue'
                        license_copy['status_class'] = 'bg-danger'
                    elif days_until == 0:
                        license_copy['status'] = 'Expires Today'
                        license_copy['status_class'] = 'bg-danger'
                    elif days_until <= 7:
                        license_copy['status'] = f'{days_until} days'
                        license_copy['status_class'] = 'bg-warning'
                    elif days_until <= 30:
                        license_copy['status'] = f'{days_until} days'
                        license_copy['status_class'] = 'bg-info'
                    else:
                        license_copy['status'] = f'{days_until} days'
                        license_copy['status_class'] = 'bg-success'
                else:
                    license_copy['status'] = 'Unknown'
                    license_copy['status_class'] = 'bg-secondary'
            else:
                license_copy['status'] = 'No Expiration'
                license_copy['status_class'] = 'bg-secondary'
            
            processed_licenses.append(license_copy)
        
        # Create filter-specific page title
        page_title = "All Licenses"
        if filter_type == 'warning':
            page_title = f"Warning Licenses (Expiring in {critical_days + 1}-{warning_days} days)"
        elif filter_type == 'critical':
            page_title = f"Critical Licenses (Expiring in 1-{critical_days} days)"
        elif filter_type == 'past_due' or filter_type == 'overdue':
            page_title = "Past Due Licenses (Expired)"
        elif filter_type == 'expiring':
            page_title = f"Upcoming Expirations (Next {upcoming_days} days)"
        elif filter_type == 'no-email':
            page_title = "Licenses Without Email Addresses"
        
        return render_template('licenses.html', 
                             licenses=processed_licenses,
                             filter_type=filter_type,
                             search_query=search_query,
                             page_title=page_title,
                             upcoming_days=upcoming_days,
                             critical_days=critical_days,
                             warning_days=warning_days,
                             company_info=COMPANY_INFO)
    except Exception as e:
        logger.error(f"Licenses page error: {e}")
        flash(f'Error loading licenses: {str(e)}', 'danger')
        return render_template('licenses.html', 
                             licenses=[],
                             filter_type='all',
                             search_query='',
                             page_title="All Licenses",
                             upcoming_days=60,
                             critical_days=7,
                             warning_days=30,
                             company_info=COMPANY_INFO)


@app.route('/license/<int:license_id>')
def view_license(license_id):
    """View single license details"""
    try:
        schema = ORACLE_CONFIG['schema']
        
        result = query_oracle(f"""
            SELECT * FROM "{schema}".LICENSES
            WHERE LIC_ID = :id
        """, {'id': license_id})
        
        if result:
            license = result[0]
            return render_template('license_detail.html', 
                                 license=license,
                                 company_info=COMPANY_INFO)
        else:
            flash('License not found', 'warning')
            return redirect(url_for('licenses'))
            
    except Exception as e:
        logger.error(f"View license error: {e}")
        flash(f'Error loading license: {str(e)}', 'danger')
        return redirect(url_for('licenses'))


@app.route('/license/<int:license_id>/edit', methods=['GET', 'POST'])
def edit_license(license_id):
    """Edit license information"""
    schema = ORACLE_CONFIG['schema']
    
    if request.method == 'GET':
        try:
            result = query_oracle(f"""
                SELECT * FROM "{schema}".LICENSES
                WHERE LIC_ID = :id
            """, {'id': license_id})
            
            if result:
                license = result[0]
                return render_template('edit_license.html', 
                                     license=license,
                                     company_info=COMPANY_INFO)
            else:
                flash('License not found', 'warning')
                return redirect(url_for('licenses'))
                
        except Exception as e:
            logger.error(f"Get license for edit error: {e}")
            flash(f'Error loading license: {str(e)}', 'danger')
            return redirect(url_for('licenses'))
    
    else:  # POST
        try:
            # Get form data
            lic_name = request.form.get('lic_name')
            lic_state = request.form.get('lic_state')
            lic_type = request.form.get('lic_type')
            lic_no = request.form.get('lic_no')
            expiration_date = request.form.get('expiration_date')
            lic_notify_names = request.form.get('lic_notify_names')
            
            # Update query
            affected = query_oracle(f"""
                UPDATE "{schema}".LICENSES
                SET LIC_NAME = :lic_name,
                    LIC_STATE = :lic_state,
                    LIC_TYPE = :lic_type,
                    LIC_NO = :lic_no,
                    EXPIRATION_DATE = TO_DATE(:expiration_date, 'YYYY-MM-DD'),
                    LIC_NOTIFY_NAMES = :lic_notify_names
                WHERE LIC_ID = :id
            """, {
                'lic_name': lic_name,
                'lic_state': lic_state,
                'lic_type': lic_type,
                'lic_no': lic_no,
                'expiration_date': expiration_date if expiration_date else None,
                'lic_notify_names': lic_notify_names,
                'id': license_id
            })
            
            flash('License updated successfully', 'success')
            return redirect(url_for('view_license', license_id=license_id))
            
        except Exception as e:
            logger.error(f"Update license error: {e}")
            flash(f'Error updating license: {str(e)}', 'danger')
            return redirect(url_for('edit_license', license_id=license_id))


@app.route('/license/<int:license_id>/delete', methods=['POST'])
def delete_license(license_id):
    """Delete a license"""
    try:
        schema = ORACLE_CONFIG['schema']
        
        # First delete related email reminders
        query_oracle(f"""
            DELETE FROM "{schema}".EMAIL_REMINDERS
            WHERE LICENSE_ID = :id
        """, {'id': license_id})
        
        # Then delete the license
        affected = query_oracle(f"""
            DELETE FROM "{schema}".LICENSES
            WHERE LIC_ID = :id
        """, {'id': license_id})
        
        if affected > 0:
            flash('License deleted successfully', 'success')
        else:
            flash('License not found', 'warning')
            
        return redirect(url_for('licenses'))
        
    except Exception as e:
        logger.error(f"Delete license error: {e}")
        flash(f'Error deleting license: {str(e)}', 'danger')
        return redirect(url_for('licenses'))


@app.route('/reminders')
def reminders():
    """View reminder history"""
    try:
        schema = ORACLE_CONFIG['schema']
        
        # Get reminder history with all necessary fields for the template
        reminders = query_oracle(f"""
            SELECT 
                er.ID as id,
                er.LICENSE_ID as license_id,
                l.LIC_NAME as lic_name,
                l.LIC_TYPE as lic_type,
                l.LIC_STATE as lic_state,
                er.REMINDER_TYPE as reminder_type,
                er.SENT_DATE as sent_date,
                er.EMAIL_TO as email_to,
                er.EMAIL_SUBJECT as subject,
                er.EMAIL_BODY as body,
                er.STATUS as status,
                NVL(l.EMAIL_ENABLED, 1) as email_enabled
            FROM "{schema}".EMAIL_REMINDERS er
            LEFT JOIN "{schema}".LICENSES l ON er.LICENSE_ID = l.LIC_ID
            ORDER BY er.SENT_DATE DESC
        """)
        
        # Get licenses needing reminders
        pending_reminders = query_oracle(f"""
            SELECT * FROM "{schema}".LICENSES_NEEDING_REMINDERS
            ORDER BY days_until_expiration
        """)
        
        return render_template('reminders.html',
                             reminders=reminders,
                             pending_reminders=pending_reminders,
                             company_info=COMPANY_INFO)
    except Exception as e:
        logger.error(f"Reminders page error: {e}")
        flash(f'Error loading reminders: {str(e)}', 'danger')
        return render_template('reminders.html',
                             reminders=[],
                             pending_reminders=[],
                             company_info=COMPANY_INFO)


@app.route('/api/stats')
def api_stats():
    """API endpoint for dashboard statistics"""
    try:
        schema = ORACLE_CONFIG['schema']
        
        stats = {}
        
        # Total licenses
        result = query_oracle(f'SELECT COUNT(*) as count FROM "{schema}".LICENSES')
        stats['total_licenses'] = result[0]['count'] if result else 0
        
        # Expiring soon
        result = query_oracle(f"""
            SELECT COUNT(*) as count FROM "{schema}".LICENSES
            WHERE EXPIRATION_DATE IS NOT NULL
            AND EXPIRATION_DATE >= SYSDATE
            AND EXPIRATION_DATE <= SYSDATE + 30
        """)
        stats['expiring_soon'] = result[0]['count'] if result else 0
        
        # Overdue
        result = query_oracle(f"""
            SELECT COUNT(*) as count FROM "{schema}".LICENSES
            WHERE EXPIRATION_DATE < SYSDATE
        """)
        stats['overdue'] = result[0]['count'] if result else 0
        
        # Reminders sent today
        result = query_oracle(f"""
            SELECT COUNT(*) as count FROM "{schema}".EMAIL_REMINDERS
            WHERE TRUNC(SENT_DATE) = TRUNC(SYSDATE)
        """)
        stats['reminders_sent_today'] = result[0]['count'] if result else 0
        
        # Licenses with emails
        result = query_oracle(f"""
            SELECT COUNT(*) as count FROM "{schema}".LICENSES
            WHERE LIC_NOTIFY_NAMES IS NOT NULL AND TRIM(LIC_NOTIFY_NAMES) IS NOT NULL
        """)
        stats['licenses_with_emails'] = result[0]['count'] if result else 0
        
        # Total reminders sent
        result = query_oracle(f'SELECT COUNT(*) as count FROM "{schema}".EMAIL_REMINDERS')
        stats['total_reminders'] = result[0]['count'] if result else 0
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"API stats error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/upcoming')
def api_upcoming():
    """API endpoint for upcoming expirations"""
    try:
        schema = ORACLE_CONFIG['schema']
        days = request.args.get('days', 90, type=int)
        
        upcoming = query_oracle(f"""
            SELECT 
                LIC_ID as id,
                LIC_NAME as lic_name,
                LIC_TYPE as lic_type,
                LIC_STATE as lic_state,
                EXPIRATION_DATE as expiration_date,
                LIC_NOTIFY_NAMES as lic_notify_names,
                TRUNC(EXPIRATION_DATE) - TRUNC(SYSDATE) as days_until_expiration
            FROM "{schema}".LICENSES
            WHERE EXPIRATION_DATE IS NOT NULL
            AND EXPIRATION_DATE >= SYSDATE
            AND EXPIRATION_DATE <= SYSDATE + :days
            ORDER BY EXPIRATION_DATE
        """, {'days': days})
        
        return jsonify(upcoming)
    except Exception as e:
        logger.error(f"API upcoming error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/license', methods=['POST'])
def api_create_license():
    """API endpoint for creating a new license"""
    try:
        schema = ORACLE_CONFIG['schema']
        data = request.get_json()
        
        # Get the next license ID
        result = query_oracle(f"""
            SELECT NVL(MAX(LIC_ID), 0) + 1 as next_id 
            FROM "{schema}".LICENSES
        """)
        next_id = result[0]['next_id'] if result else 1
        
        # Insert new license
        query_oracle(f"""
            INSERT INTO "{schema}".LICENSES (
                LIC_ID,
                LIC_NAME,
                LIC_STATE,
                LIC_TYPE,
                LIC_NO,
                ASCEM_NO,
                FIRST_ISSUE_DATE,
                EXPIRATION_DATE,
                LIC_NOTIFY_NAMES,
                LIC_COMMENTS,
                EMAIL_ENABLED
            ) VALUES (
                :lic_id,
                :lic_name,
                :lic_state,
                :lic_type,
                :lic_no,
                :ascem_no,
                CASE WHEN :first_issue_date IS NOT NULL THEN TO_DATE(:first_issue_date, 'YYYY-MM-DD') ELSE NULL END,
                CASE WHEN :expiration_date IS NOT NULL THEN TO_DATE(:expiration_date, 'YYYY-MM-DD') ELSE NULL END,
                :lic_notify_names,
                :lic_comments,
                1
            )
        """, {
            'lic_id': next_id,
            'lic_name': data.get('lic_name'),
            'lic_state': data.get('lic_state'),
            'lic_type': data.get('lic_type'),
            'lic_no': data.get('lic_no'),
            'ascem_no': data.get('ascem_no'),
            'first_issue_date': data.get('first_issue_date'),
            'expiration_date': data.get('expiration_date'),
            'lic_notify_names': data.get('lic_notify_names'),
            'lic_comments': data.get('lic_comments')
        })
        
        return jsonify({'success': True, 'id': next_id})
        
    except Exception as e:
        logger.error(f"API create license error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/license/<int:license_id>', methods=['GET', 'PUT', 'DELETE'])
def api_license(license_id):
    """API endpoint for single license operations"""
    schema = ORACLE_CONFIG['schema']
    
    if request.method == 'GET':
        try:
            result = query_oracle(f"""
                SELECT 
                    LIC_ID,
                    LIC_NAME,
                    LIC_STATE,
                    LIC_TYPE,
                    LIC_NO,
                    ASCEM_NO,
                    FIRST_ISSUE_DATE,
                    EXPIRATION_DATE,
                    LIC_NOTIFY_NAMES,
                    LIC_COMMENTS,
                    EMAIL_ENABLED
                FROM "{schema}".LICENSES
                WHERE LIC_ID = :id
            """, {'id': license_id})
            
            if result:
                return jsonify(result[0])
            else:
                return jsonify({'error': 'License not found'}), 404
                
        except Exception as e:
            logger.error(f"API get license error: {e}")
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            affected = query_oracle(f"""
                UPDATE "{schema}".LICENSES
                SET LIC_NAME = :lic_name,
                    LIC_STATE = :lic_state,
                    LIC_TYPE = :lic_type,
                    LIC_NO = :lic_no,
                    ASCEM_NO = :ascem_no,
                    FIRST_ISSUE_DATE = CASE WHEN :first_issue_date IS NOT NULL THEN TO_DATE(:first_issue_date, 'YYYY-MM-DD') ELSE NULL END,
                    EXPIRATION_DATE = CASE WHEN :expiration_date IS NOT NULL THEN TO_DATE(:expiration_date, 'YYYY-MM-DD') ELSE NULL END,
                    LIC_NOTIFY_NAMES = :lic_notify_names,
                    LIC_COMMENTS = :lic_comments
                WHERE LIC_ID = :id
            """, {
                'lic_name': data.get('lic_name'),
                'lic_state': data.get('lic_state'),
                'lic_type': data.get('lic_type'),
                'lic_no': data.get('lic_no'),
                'ascem_no': data.get('ascem_no'),
                'first_issue_date': data.get('first_issue_date'),
                'expiration_date': data.get('expiration_date'),
                'lic_notify_names': data.get('lic_notify_names'),
                'lic_comments': data.get('lic_comments'),
                'id': license_id
            })
            
            return jsonify({'success': True, 'affected': affected})
            
        except Exception as e:
            logger.error(f"API update license error: {e}")
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            # Delete related reminders first
            query_oracle(f"""
                DELETE FROM "{schema}".EMAIL_REMINDERS
                WHERE LICENSE_ID = :id
            """, {'id': license_id})
            
            # Delete the license
            affected = query_oracle(f"""
                DELETE FROM "{schema}".LICENSES
                WHERE LIC_ID = :id
            """, {'id': license_id})
            
            return jsonify({'success': True, 'affected': affected})
            
        except Exception as e:
            logger.error(f"API delete license error: {e}")
            return jsonify({'error': str(e)}), 500


@app.route('/api/license-types')
def api_license_types():
    """API endpoint to get unique license types"""
    try:
        schema = ORACLE_CONFIG['schema']
        
        types = query_oracle(f"""
            SELECT DISTINCT LIC_TYPE 
            FROM "{schema}".LICENSES 
            WHERE LIC_TYPE IS NOT NULL
            ORDER BY LIC_TYPE
        """)
        
        # Extract just the type values
        type_list = [t['lic_type'] for t in types if t['lic_type']]
        return jsonify(type_list)
    except Exception as e:
        logger.error(f"API license types error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/license-states')
def api_license_states():
    """API endpoint to get unique license states"""
    try:
        schema = ORACLE_CONFIG['schema']
        
        states = query_oracle(f"""
            SELECT DISTINCT LIC_STATE 
            FROM "{schema}".LICENSES 
            WHERE LIC_STATE IS NOT NULL
            ORDER BY LIC_STATE
        """)
        
        # Extract just the state values
        state_list = [s['lic_state'] for s in states if s['lic_state']]
        return jsonify(state_list)
    except Exception as e:
        logger.error(f"API license states error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/license/<int:license_id>/toggle-emails', methods=['POST'])
def api_toggle_emails(license_id):
    """API endpoint to toggle email notifications for a license"""
    try:
        schema = ORACLE_CONFIG['schema']
        
        # Check if license exists and get current email status
        license = query_oracle(f"""
            SELECT LIC_ID, LIC_NAME, EMAIL_ENABLED
            FROM "{schema}".LICENSES
            WHERE LIC_ID = :id
        """, {'id': license_id})
        
        if not license:
            return jsonify({'error': 'License not found'}), 404
        
        # Toggle the email_enabled status (default to true if not set)
        current_status = license[0].get('email_enabled', 1)
        new_status = 0 if current_status else 1
        
        # Update the license
        query_oracle(f"""
            UPDATE "{schema}".LICENSES
            SET EMAIL_ENABLED = :status
            WHERE LIC_ID = :id
        """, {'status': new_status, 'id': license_id})
        
        status_text = "enabled" if new_status else "disabled"
        return jsonify({
            'success': True,
            'email_enabled': bool(new_status),
            'message': f"Email reminders have been {status_text} for this license"
        })
        
    except Exception as e:
        logger.error(f"API toggle emails error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/send-reminders', methods=['POST'])
def api_send_reminders():
    """API endpoint to send email reminders for selected licenses"""
    try:
        data = request.get_json()
        license_ids = data.get('license_ids', [])
        
        if not license_ids:
            return jsonify({'error': 'No licenses selected'}), 400
        
        schema = ORACLE_CONFIG['schema']
        sent_count = 0
        failed_count = 0
        
        # Get filter parameters from request or use defaults
        critical_days = int(request.args.get('critical_days', 7))
        warning_days = int(request.args.get('warning_days', 30))
        
        # Get SMTP configuration
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        sender_email = os.getenv('SENDER_EMAIL', smtp_username)
        
        # Get license details for selected IDs
        placeholders = ','.join([f':id{i}' for i in range(len(license_ids))])
        params = {f'id{i}': lid for i, lid in enumerate(license_ids)}
        
        licenses = query_oracle(f"""
            SELECT 
                LIC_ID as id,
                LIC_NAME as lic_name,
                LIC_TYPE as lic_type,
                LIC_STATE as lic_state,
                LIC_NO as lic_no,
                EXPIRATION_DATE as expiration_date,
                LIC_NOTIFY_NAMES as lic_notify_names,
                TRUNC(EXPIRATION_DATE) - TRUNC(SYSDATE) as days_until_expiration
            FROM "{schema}".LICENSES
            WHERE LIC_ID IN ({placeholders})
        """, params)
        
        for license in licenses:
            # Determine reminder type based on days until expiration
            days_left = license.get('days_until_expiration', 0)
            if days_left <= critical_days:
                reminder_type = 'critical'
            elif days_left <= warning_days:
                reminder_type = 'warning'
            else:
                reminder_type = 'upcoming'
            
            # Prepare email details
            email_to = license.get('lic_notify_names') or ''
            email_to = email_to.strip() if email_to else ''
            if not email_to:
                email_to = COMPANY_INFO['support_email']
            
            email_subject = f"License Renewal Reminder: {license['lic_name']} - {days_left} days remaining"
            
            email_body = f"""
Dear License Administrator,

This is a reminder that the following license is expiring soon:

License Name: {license['lic_name']}
License Type: {license.get('lic_type', 'N/A')}
License State: {license.get('lic_state', 'N/A')}
License Number: {license.get('lic_no', 'N/A')}
Expiration Date: {license.get('expiration_date', 'N/A')}
Days Until Expiration: {days_left}

Please take appropriate action to renew this license before it expires.

Best regards,
{COMPANY_INFO['name']}
{COMPANY_INFO['website']}
            """
            
            # Try to send email
            email_status = 'failed'
            try:
                # Only attempt SMTP if credentials are configured
                if smtp_username and smtp_password:
                    msg = MIMEMultipart()
                    msg['From'] = sender_email
                    msg['To'] = email_to
                    msg['Subject'] = email_subject
                    msg.attach(MIMEText(email_body, 'plain'))
                    
                    with smtplib.SMTP(smtp_server, smtp_port) as server:
                        server.starttls()
                        server.login(smtp_username, smtp_password)
                        server.send_message(msg)
                    
                    email_status = 'sent'
                    sent_count += 1
                    logger.info(f"Email sent successfully for license {license['id']}")
                else:
                    # SMTP not configured, but we'll still log it
                    logger.warning(f"SMTP not configured, marking email as failed for license {license['id']}")
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to send email for license {license['id']}: {e}")
                failed_count += 1
            
            # Always log to EMAIL_REMINDERS table regardless of success/failure
            try:
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
                logger.info(f"Email history logged for license {license['id']} with status: {email_status}")
            except Exception as e:
                logger.error(f"Failed to log email history for license {license['id']}: {e}")
        
        return jsonify({
            'success': True,
            'sent': sent_count,
            'failed': failed_count,
            'total': len(licenses)
        })
        
    except Exception as e:
        logger.error(f"API send reminders error: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('base.html', company_info=COMPANY_INFO), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {e}")
    return render_template('base.html', company_info=COMPANY_INFO), 500


def main():
    """Run the Flask application"""
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting License Reminder Dashboard (Oracle) on port {port}")
    logger.info(f"Oracle Host: {ORACLE_CONFIG['host']}")
    logger.info(f"Oracle Schema: {ORACLE_CONFIG['schema']}")
    
    try:
        # Test Oracle connection
        conn = get_oracle_connection()
        conn.close()
        logger.info("✓ Oracle connection successful")
    except Exception as e:
        logger.error(f"✗ Oracle connection failed: {e}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)


if __name__ == '__main__':
    main()