"""
Web Dashboard for License Reminder System - Oracle Database Version
Flask-based web interface for viewing license data and reminders
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from dotenv import load_dotenv
import oracledb

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


@app.route('/')
def dashboard():
    """Main dashboard page"""
    try:
        schema = ORACLE_CONFIG['schema']
        
        # Get statistics
        stats = {
            'total_licenses': 0,
            'expiring_soon': 0,
            'overdue': 0,
            'reminders_sent_today': 0
        }
        
        # Total licenses
        result = query_oracle(f'SELECT COUNT(*) as count FROM "{schema}".LICENSES')
        if result:
            stats['total_licenses'] = result[0]['count']
        
        # Expiring soon (next 30 days)
        result = query_oracle(f"""
            SELECT COUNT(*) as count FROM "{schema}".UPCOMING_EXPIRATIONS
            WHERE days_until_expiration <= 30
        """)
        if result:
            stats['expiring_soon'] = result[0]['count']
        
        # Overdue
        result = query_oracle(f'SELECT COUNT(*) as count FROM "{schema}".OVERDUE_LICENSES')
        if result:
            stats['overdue'] = result[0]['count']
        
        # Reminders sent today
        result = query_oracle(f"""
            SELECT COUNT(*) as count FROM "{schema}".EMAIL_REMINDERS
            WHERE TRUNC(SENT_DATE) = TRUNC(SYSDATE)
        """)
        if result:
            stats['reminders_sent_today'] = result[0]['count']
        
        # Get recent licenses needing reminders
        upcoming_reminders = query_oracle(f"""
            SELECT * FROM (
                SELECT * FROM "{schema}".LICENSES_NEEDING_REMINDERS
                ORDER BY days_until_expiration
            ) WHERE ROWNUM <= 10
        """)
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             upcoming_reminders=upcoming_reminders,
                             company_info=COMPANY_INFO)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        return render_template('dashboard.html', 
                             stats={'total_licenses': 0, 'expiring_soon': 0, 'overdue': 0, 'reminders_sent_today': 0},
                             upcoming_reminders=[],
                             company_info=COMPANY_INFO)


@app.route('/licenses')
def licenses():
    """View all licenses"""
    try:
        schema = ORACLE_CONFIG['schema']
        
        # Get filter parameters
        filter_type = request.args.get('filter', 'all')
        search_query = request.args.get('search', '')
        
        # Build query based on filter
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
                LIC_NOTIFY_NAMES as lic_notify_names
            FROM "{schema}".LICENSES
        """
        
        where_conditions = []
        
        if filter_type == 'expiring':
            where_conditions.append("""
                EXPIRATION_DATE IS NOT NULL 
                AND EXPIRATION_DATE >= SYSDATE 
                AND EXPIRATION_DATE <= SYSDATE + 30
            """)
        elif filter_type == 'overdue':
            where_conditions.append("EXPIRATION_DATE < SYSDATE")
        elif filter_type == 'no-email':
            where_conditions.append("LIC_NOTIFY_NAMES IS NULL OR LENGTH(TRIM(LIC_NOTIFY_NAMES)) = 0")
        
        if search_query:
            where_conditions.append(f"""
                (UPPER(LIC_NAME) LIKE UPPER('%{search_query}%')
                OR UPPER(LIC_TYPE) LIKE UPPER('%{search_query}%')
                OR UPPER(LIC_STATE) LIKE UPPER('%{search_query}%')
                OR UPPER(LIC_NO) LIKE UPPER('%{search_query}%'))
            """)
        
        if where_conditions:
            base_query += " WHERE " + " AND ".join(where_conditions)
        
        base_query += " ORDER BY EXPIRATION_DATE NULLS LAST, LIC_NAME"
        
        all_licenses = query_oracle(base_query)
        
        # Process licenses to add status information
        processed_licenses = []
        for license in all_licenses:
            license_copy = license.copy()
            
            # Calculate status
            if license.get('expiration_date'):
                exp_date = datetime.fromisoformat(license['expiration_date']) if isinstance(license['expiration_date'], str) else license['expiration_date']
                today = datetime.now()
                days_until = (exp_date - today).days
                
                license_copy['days_until_expiration'] = days_until
                
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
                license_copy['status'] = 'No Expiration'
                license_copy['status_class'] = 'bg-secondary'
            
            processed_licenses.append(license_copy)
        
        return render_template('licenses.html', 
                             licenses=processed_licenses,
                             filter_type=filter_type,
                             search_query=search_query,
                             company_info=COMPANY_INFO)
    except Exception as e:
        logger.error(f"Licenses page error: {e}")
        flash(f'Error loading licenses: {str(e)}', 'danger')
        return render_template('licenses.html', 
                             licenses=[],
                             filter_type='all',
                             search_query='',
                             company_info=COMPANY_INFO)


@app.route('/reminders')
def reminders():
    """View reminder history"""
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
        pending_reminders = query_oracle(f"""
            SELECT * FROM "{schema}".LICENSES_NEEDING_REMINDERS
            ORDER BY days_until_expiration
        """)
        
        return render_template('reminders.html',
                             reminder_history=reminder_history,
                             pending_reminders=pending_reminders,
                             company_info=COMPANY_INFO)
    except Exception as e:
        logger.error(f"Reminders page error: {e}")
        flash(f'Error loading reminders: {str(e)}', 'danger')
        return render_template('reminders.html',
                             reminder_history=[],
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
            SELECT COUNT(*) as count FROM "{schema}".UPCOMING_EXPIRATIONS
            WHERE days_until_expiration <= 30
        """)
        stats['expiring_soon'] = result[0]['count'] if result else 0
        
        # Overdue
        result = query_oracle(f'SELECT COUNT(*) as count FROM "{schema}".OVERDUE_LICENSES')
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
            WHERE LIC_NOTIFY_NAMES IS NOT NULL AND LENGTH(TRIM(LIC_NOTIFY_NAMES)) > 0
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
            SELECT * FROM "{schema}".UPCOMING_EXPIRATIONS
            WHERE days_until_expiration <= :days
            ORDER BY expiration_date
        """, {'days': days})
        
        return jsonify(upcoming)
    except Exception as e:
        logger.error(f"API upcoming error: {e}")
        return jsonify({'error': str(e)}), 500


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