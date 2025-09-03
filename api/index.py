#!/usr/bin/env python3
"""
License Dashboard Web Interface - Vercel Serverless Function (Oracle Version)
Flask-based web UI for viewing upcoming license expirations using Oracle Database
"""

import os
import sys
from flask import Flask, render_template, jsonify, request, flash, redirect, url_for
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging
import oracledb

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder='../templates')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-change-this')

# Oracle configuration
ORACLE_CONFIG = {
    'host': os.getenv('ORACLE_HOST'),
    'port': int(os.getenv('ORACLE_PORT', 1521)),
    'service': os.getenv('ORACLE_SERVICE_NAME'),
    'user': os.getenv('ORACLE_USER', 'SYS'),
    'password': os.getenv('ORACLE_PASSWORD'),
    'schema': os.getenv('ORACLE_SCHEMA')
}

# Check Oracle configuration
if not all([ORACLE_CONFIG['host'], ORACLE_CONFIG['password'], ORACLE_CONFIG['schema']]):
    logger.error("Oracle configuration missing!")

@app.context_processor
def inject_current_date():
    """Make current date available to all templates"""
    return dict(current_date=datetime.now())

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
        
        columns = [col[0].lower() for col in cursor.description]
        results = []
        
        for row in cursor:
            result_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                # Convert Oracle datetime to Python datetime string for JSON serialization
                if isinstance(value, datetime):
                    value = value.isoformat()
                result_dict[col] = value
            results.append(result_dict)
        
        cursor.close()
        connection.close()
        
        return results
        
    except Exception as e:
        logger.error(f"Query error: {e}")
        return []

def get_upcoming_expirations():
    """Get all upcoming license expirations from Oracle"""
    try:
        schema = ORACLE_CONFIG['schema']
        return query_oracle(f"""
            SELECT * FROM "{schema}".UPCOMING_EXPIRATIONS
            ORDER BY expiration_date
        """)
    except Exception as e:
        logger.error(f"Error fetching upcoming expirations: {e}")
        return []

def get_license_statistics():
    """Get license statistics for dashboard from Oracle"""
    try:
        schema = ORACLE_CONFIG['schema']
        stats = {
            'total_licenses': 0,
            'upcoming_expirations': 0,
            'critical_count': 0,
            'warning_count': 0,
            'past_due_count': 0
        }
        
        # Total licenses
        result = query_oracle(f'SELECT COUNT(*) as count FROM "{schema}".LICENSES')
        if result:
            stats['total_licenses'] = result[0]['count']
        
        # Upcoming expirations (next 35 days)
        result = query_oracle(f"""
            SELECT COUNT(*) as count FROM "{schema}".LICENSES
            WHERE EXPIRATION_DATE IS NOT NULL
            AND EXPIRATION_DATE >= SYSDATE
            AND EXPIRATION_DATE <= SYSDATE + 35
        """)
        if result:
            stats['upcoming_expirations'] = result[0]['count']
        
        # Critical (next 10 days)
        result = query_oracle(f"""
            SELECT COUNT(*) as count FROM "{schema}".LICENSES
            WHERE EXPIRATION_DATE >= SYSDATE
            AND EXPIRATION_DATE <= SYSDATE + 10
        """)
        if result:
            stats['critical_count'] = result[0]['count']
        
        # Warning (next 30 days)
        result = query_oracle(f"""
            SELECT COUNT(*) as count FROM "{schema}".LICENSES
            WHERE EXPIRATION_DATE >= SYSDATE
            AND EXPIRATION_DATE <= SYSDATE + 30
        """)
        if result:
            stats['warning_count'] = result[0]['count']
        
        # Past due (expired licenses)
        result = query_oracle(f"""
            SELECT COUNT(*) as count FROM "{schema}".OVERDUE_LICENSES
        """)
        if result:
            stats['past_due_count'] = result[0]['count']
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return {
            'total_licenses': 0,
            'upcoming_expirations': 0,
            'critical_count': 0,
            'warning_count': 0,
            'past_due_count': 0
        }

def get_reminder_statistics():
    """Get reminder statistics from Oracle"""
    try:
        schema = ORACLE_CONFIG['schema']
        
        # Get today's reminders
        today_result = query_oracle(f"""
            SELECT COUNT(*) as count FROM "{schema}".EMAIL_REMINDERS
            WHERE TRUNC(SENT_DATE) = TRUNC(SYSDATE)
        """)
        today_count = today_result[0]['count'] if today_result else 0
        
        # Get total reminders
        total_result = query_oracle(f"""
            SELECT COUNT(*) as count FROM "{schema}".EMAIL_REMINDERS
        """)
        total_count = total_result[0]['count'] if total_result else 0
        
        # Get pending reminders
        pending_result = query_oracle(f"""
            SELECT COUNT(*) as count FROM "{schema}".LICENSES_NEEDING_REMINDERS
        """)
        pending_count = pending_result[0]['count'] if pending_result else 0
        
        return {
            'sent_today': today_count,
            'total_sent': total_count,
            'pending': pending_count
        }
        
    except Exception as e:
        logger.error(f"Error getting reminder statistics: {e}")
        return {
            'sent_today': 0,
            'total_sent': 0,
            'pending': 0
        }

@app.route('/')
def dashboard():
    """Main dashboard showing overview statistics"""
    try:
        stats = get_license_statistics()
        reminder_stats = get_reminder_statistics()
        schema = ORACLE_CONFIG['schema']
        
        # Get critical upcoming expirations
        critical_licenses = query_oracle(f"""
            SELECT * FROM (
                SELECT * FROM "{schema}".UPCOMING_EXPIRATIONS
                WHERE status_category IN ('critical', 'warning')
                ORDER BY expiration_date
            ) WHERE ROWNUM <= 10
        """)
        
        return render_template('dashboard.html', 
                             stats=stats,
                             reminder_stats=reminder_stats,
                             critical_licenses=critical_licenses)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        flash('Error loading dashboard. Database may not be configured.', 'danger')
        return render_template('dashboard.html', 
                             stats={'total_licenses': 0, 'upcoming_expirations': 0, 'critical_count': 0, 'warning_count': 0, 'past_due_count': 0},
                             reminder_stats={'sent_today': 0, 'total_sent': 0, 'pending': 0},
                             critical_licenses=[])

@app.route('/licenses')
def licenses():
    """View all licenses with filtering options"""
    try:
        schema = ORACLE_CONFIG['schema']
        
        # Get filter parameter
        filter_type = request.args.get('filter', 'upcoming')
        
        if filter_type == 'all':
            # Get all licenses
            all_licenses = query_oracle(f"""
                SELECT 
                    LIC_ID as id,
                    LIC_NAME as lic_name,
                    LIC_STATE as lic_state,
                    LIC_TYPE as lic_type,
                    LIC_NO as lic_no,
                    ASCEM_NO as ascem_no,
                    FIRST_ISSUE_DATE as first_issue_date,
                    EXPIRATION_DATE as expiration_date,
                    LIC_NOTIFY_NAMES as lic_notify_names
                FROM "{schema}".LICENSES
                ORDER BY EXPIRATION_DATE NULLS LAST, LIC_NAME
            """)
        elif filter_type == 'expired':
            # Get expired licenses
            all_licenses = query_oracle(f"""
                SELECT 
                    id,
                    lic_name,
                    lic_state,
                    lic_type,
                    lic_no,
                    ascem_no,
                    first_issue_date,
                    expiration_date,
                    lic_notify_names,
                    days_overdue
                FROM "{schema}".OVERDUE_LICENSES
                ORDER BY expiration_date DESC
            """)
        else:  # upcoming (default)
            # Get upcoming expirations (next 35 days)
            all_licenses = query_oracle(f"""
                SELECT 
                    id,
                    lic_name,
                    lic_state,
                    lic_type,
                    lic_no,
                    ascem_no,
                    first_issue_date,
                    expiration_date,
                    lic_notify_names,
                    days_until_expiration,
                    status_category
                FROM "{schema}".UPCOMING_EXPIRATIONS
                WHERE days_until_expiration <= 35
                ORDER BY expiration_date
            """)
        
        # Process licenses to add display information
        processed_licenses = []
        for license in all_licenses:
            license_copy = license.copy()
            
            # Add status class for display
            if license.get('status_category'):
                if license['status_category'] == 'critical':
                    license_copy['status_class'] = 'bg-danger'
                elif license['status_category'] == 'warning':
                    license_copy['status_class'] = 'bg-warning'
                elif license['status_category'] == 'upcoming':
                    license_copy['status_class'] = 'bg-info'
                else:
                    license_copy['status_class'] = 'bg-success'
            elif license.get('days_overdue'):
                license_copy['status_class'] = 'bg-danger'
                license_copy['status_category'] = 'expired'
            elif license.get('expiration_date'):
                # Calculate days until expiration for 'all' filter
                if isinstance(license['expiration_date'], str):
                    exp_date = datetime.fromisoformat(license['expiration_date'])
                else:
                    exp_date = license['expiration_date']
                
                days_until = (exp_date - datetime.now()).days
                license_copy['days_until_expiration'] = days_until
                
                if days_until < 0:
                    license_copy['status_class'] = 'bg-danger'
                    license_copy['status_category'] = 'expired'
                elif days_until <= 10:
                    license_copy['status_class'] = 'bg-danger'
                    license_copy['status_category'] = 'critical'
                elif days_until <= 30:
                    license_copy['status_class'] = 'bg-warning'
                    license_copy['status_category'] = 'warning'
                elif days_until <= 60:
                    license_copy['status_class'] = 'bg-info'
                    license_copy['status_category'] = 'upcoming'
                else:
                    license_copy['status_class'] = 'bg-success'
                    license_copy['status_category'] = 'normal'
            else:
                license_copy['status_class'] = 'bg-secondary'
                license_copy['status_category'] = 'no_expiration'
            
            processed_licenses.append(license_copy)
        
        return render_template('licenses.html', 
                             licenses=processed_licenses,
                             filter_type=filter_type)
    except Exception as e:
        logger.error(f"Licenses page error: {e}")
        flash('Error loading licenses. Database may not be configured.', 'danger')
        return render_template('licenses.html', 
                             licenses=[],
                             filter_type='upcoming')

@app.route('/reminders')
def reminders():
    """View reminder history and pending reminders"""
    try:
        schema = ORACLE_CONFIG['schema']
        
        # Get reminder history
        reminder_history = query_oracle(f"""
            SELECT 
                er.ID,
                er.LICENSE_ID,
                l.LIC_NAME,
                l.LIC_TYPE,
                er.REMINDER_TYPE,
                er.SENT_DATE,
                er.EMAIL_TO,
                er.STATUS
            FROM "{schema}".EMAIL_REMINDERS er
            LEFT JOIN "{schema}".LICENSES l ON er.LICENSE_ID = l.LIC_ID
            ORDER BY er.SENT_DATE DESC
        """)
        
        # Get licenses needing reminders
        licenses_needing = query_oracle(f"""
            SELECT * FROM "{schema}".LICENSES_NEEDING_REMINDERS
            ORDER BY days_until_expiration
        """)
        
        return render_template('reminders.html',
                             reminder_history=reminder_history,
                             licenses_needing=licenses_needing)
    except Exception as e:
        logger.error(f"Reminders page error: {e}")
        flash('Error loading reminders. Database may not be configured.', 'danger')
        return render_template('reminders.html',
                             reminder_history=[],
                             licenses_needing=[])

@app.route('/api/stats')
def api_stats():
    """API endpoint returning dashboard statistics in JSON"""
    try:
        stats = get_license_statistics()
        reminder_stats = get_reminder_statistics()
        
        # Combine all statistics
        all_stats = {**stats, **reminder_stats}
        
        return jsonify(all_stats)
    except Exception as e:
        logger.error(f"API stats error: {e}")
        return jsonify({'error': 'Database not configured'}), 500

@app.route('/api/upcoming')
def api_upcoming():
    """API endpoint returning upcoming expirations in JSON"""
    try:
        schema = ORACLE_CONFIG['schema']
        days = request.args.get('days', 35, type=int)
        
        upcoming = query_oracle(f"""
            SELECT * FROM "{schema}".UPCOMING_EXPIRATIONS
            WHERE days_until_expiration <= :days
            ORDER BY expiration_date
        """, {'days': days})
        
        return jsonify(upcoming)
    except Exception as e:
        logger.error(f"API upcoming error: {e}")
        return jsonify({'error': 'Database not configured'}), 500

@app.route('/api/licenses-needing-reminders')
def api_licenses_needing_reminders():
    """API endpoint for licenses needing reminders"""
    try:
        schema = ORACLE_CONFIG['schema']
        
        licenses = query_oracle(f"""
            SELECT * FROM "{schema}".LICENSES_NEEDING_REMINDERS
            ORDER BY days_until_expiration
        """)
        
        return jsonify(licenses)
    except Exception as e:
        logger.error(f"API licenses needing reminders error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint for monitoring"""
    try:
        # Test Oracle connection
        connection = get_oracle_connection()
        connection.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Handler for Vercel
handler = app