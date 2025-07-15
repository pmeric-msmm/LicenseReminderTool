#!/usr/bin/env python3
"""
License Dashboard Web Interface - Vercel Serverless Function
Flask-based web UI for viewing upcoming license expirations
"""

import os
import sys
from flask import Flask, render_template, jsonify, request, flash, redirect, url_for
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime, timedelta
import logging

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

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

if not supabase_url or not supabase_key:
    logger.error("Supabase configuration missing!")

supabase: Client = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None

@app.context_processor
def inject_current_date():
    """Make current date available to all templates"""
    return dict(current_date=datetime.now())

def get_upcoming_expirations():
    """Get all upcoming license expirations"""
    if not supabase:
        return []
    try:
        result = supabase.table('upcoming_expirations').select('*').execute()
        return result.data
    except Exception as e:
        logger.error(f"Error fetching upcoming expirations: {e}")
        return []

def get_license_statistics():
    """Get license statistics for dashboard"""
    if not supabase:
        return {
            'total_licenses': 0,
            'upcoming_expirations': 0,
            'critical_count': 0,
            'warning_count': 0,
            'past_due_count': 0
        }
    try:
        # Total licenses
        total_result = supabase.table('licenses').select('id', count='exact').execute()
        total_licenses = total_result.count
        
        # Upcoming expirations (next 35 days) - Use consistent logic with filter
        today = datetime.now().strftime('%Y-%m-%d')
        cutoff_date_35 = (datetime.now() + timedelta(days=35)).strftime('%Y-%m-%d')
        upcoming_result = supabase.table('licenses').select('id', count='exact')\
            .gte('expiration_date', today)\
            .lte('expiration_date', cutoff_date_35)\
            .not_.is_('expiration_date', 'null')\
            .execute()
        upcoming_count = upcoming_result.count
        
        # Critical (next 10 days)
        critical_result = supabase.table('licenses').select('id', count='exact')\
            .gte('expiration_date', datetime.now().strftime('%Y-%m-%d'))\
            .lte('expiration_date', (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d'))\
            .execute()
        critical_count = critical_result.count
        
        # Warning (next 30 days)
        warning_result = supabase.table('licenses').select('id', count='exact')\
            .gte('expiration_date', datetime.now().strftime('%Y-%m-%d'))\
            .lte('expiration_date', (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'))\
            .execute()
        warning_count = warning_result.count
        
        # Past due (expired licenses)
        past_due_result = supabase.table('licenses').select('id', count='exact')\
            .lt('expiration_date', datetime.now().strftime('%Y-%m-%d'))\
            .not_.is_('expiration_date', 'null')\
            .execute()
        past_due_count = past_due_result.count
        
        return {
            'total_licenses': total_licenses,
            'upcoming_expirations': upcoming_count,
            'critical_count': critical_count,
            'warning_count': warning_count,
            'past_due_count': past_due_count
        }
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        return {
            'total_licenses': 0,
            'upcoming_expirations': 0,
            'critical_count': 0,
            'warning_count': 0,
            'past_due_count': 0
        }

def get_license_statistics_filtered(upcoming_days=35, critical_days=10, warning_days=30):
    """Get license statistics for dashboard with custom filter parameters"""
    if not supabase:
        return {
            'total_licenses': 0,
            'upcoming_expirations': 0,
            'critical_count': 0,
            'warning_count': 0,
            'past_due_count': 0
        }
    try:
        # Total licenses
        total_result = supabase.table('licenses').select('id', count='exact').execute()
        total_licenses = total_result.count
        
        # Upcoming expirations (custom days)
        today = datetime.now().strftime('%Y-%m-%d')
        cutoff_date_upcoming = (datetime.now() + timedelta(days=upcoming_days)).strftime('%Y-%m-%d')
        upcoming_result = supabase.table('licenses').select('id', count='exact')\
            .gte('expiration_date', today)\
            .lte('expiration_date', cutoff_date_upcoming)\
            .not_.is_('expiration_date', 'null')\
            .execute()
        upcoming_count = upcoming_result.count
        
        # Critical (custom days)
        cutoff_date_critical = (datetime.now() + timedelta(days=critical_days)).strftime('%Y-%m-%d')
        critical_result = supabase.table('licenses').select('id', count='exact')\
            .gte('expiration_date', today)\
            .lte('expiration_date', cutoff_date_critical)\
            .not_.is_('expiration_date', 'null')\
            .execute()
        critical_count = critical_result.count
        
        # Warning (custom days)
        cutoff_date_warning = (datetime.now() + timedelta(days=warning_days)).strftime('%Y-%m-%d')
        warning_result = supabase.table('licenses').select('id', count='exact')\
            .gte('expiration_date', today)\
            .lte('expiration_date', cutoff_date_warning)\
            .not_.is_('expiration_date', 'null')\
            .execute()
        warning_count = warning_result.count
        
        # Past due (expired licenses)
        past_due_result = supabase.table('licenses').select('id', count='exact')\
            .lt('expiration_date', today)\
            .not_.is_('expiration_date', 'null')\
            .execute()
        past_due_count = past_due_result.count
        
        return {
            'total_licenses': total_licenses,
            'upcoming_expirations': upcoming_count,
            'critical_count': critical_count,
            'warning_count': warning_count,
            'past_due_count': past_due_count
        }
    except Exception as e:
        logger.error(f"Error fetching filtered statistics: {e}")
        return {
            'total_licenses': 0,
            'upcoming_expirations': 0,
            'critical_count': 0,
            'warning_count': 0,
            'past_due_count': 0
        }

def get_all_licenses():
    """Get all licenses"""
    if not supabase:
        return []
    try:
        result = supabase.table('licenses').select('*').order('expiration_date').execute()
        
        # Add status calculation to each license
        licenses_with_status = []
        for license in result.data:
            license_copy = license.copy()
            
            if license_copy.get('expiration_date'):
                exp_date = datetime.strptime(license_copy['expiration_date'], '%Y-%m-%d')
                today = datetime.now()
                days_until = (exp_date - today).days
                
                if days_until < 0:
                    license_copy['status_category'] = 'Expired'
                    license_copy['status_class'] = 'bg-danger'
                    license_copy['days_overdue'] = abs(days_until)
                elif days_until <= 10:
                    license_copy['status_category'] = 'Critical'
                    license_copy['status_class'] = 'bg-danger'
                elif days_until <= 30:
                    license_copy['status_category'] = 'Warning'
                    license_copy['status_class'] = 'bg-warning'
                elif days_until <= 90:
                    license_copy['status_category'] = 'Active'
                    license_copy['status_class'] = 'bg-info'
                else:
                    license_copy['status_category'] = 'Active'
                    license_copy['status_class'] = 'bg-success'
            else:
                license_copy['status_category'] = 'No Expiration'
                license_copy['status_class'] = 'bg-secondary'
            
            licenses_with_status.append(license_copy)
        
        return licenses_with_status
    except Exception as e:
        logger.error(f"Error fetching all licenses: {e}")
        return []

def get_past_due_licenses():
    """Get all past due licenses"""
    if not supabase:
        return []
    try:
        result = supabase.table('licenses').select('*')\
            .lt('expiration_date', datetime.now().strftime('%Y-%m-%d'))\
            .not_.is_('expiration_date', 'null')\
            .order('expiration_date')\
            .execute()
        
        # Add days overdue calculation
        past_due_licenses = []
        for license in result.data:
            license_copy = license.copy()
            if license_copy.get('expiration_date'):
                exp_date = datetime.strptime(license_copy['expiration_date'], '%Y-%m-%d')
                days_overdue = (datetime.now() - exp_date).days
                license_copy['days_overdue'] = days_overdue
            past_due_licenses.append(license_copy)
        
        return past_due_licenses
    except Exception as e:
        logger.error(f"Error fetching past due licenses: {e}")
        return []

def get_sent_reminders():
    """Get sent reminder history"""
    if not supabase:
        return []
    try:
        result = supabase.table('email_reminders')\
            .select('*, licenses(lic_name, lic_type, lic_state, email_enabled)')\
            .order('sent_date', desc=True)\
            .limit(50)\
            .execute()
        return result.data
    except Exception as e:
        logger.error(f"Error fetching reminders: {e}")
        return []

@app.route('/')
def dashboard():
    """Main dashboard page"""
    filter_upcoming = request.args.get('upcoming_days', 35)
    filter_critical = request.args.get('critical_days', 10)
    filter_warning = request.args.get('warning_days', 30)

    stats = get_license_statistics_filtered(
        upcoming_days=int(filter_upcoming),
        critical_days=int(filter_critical),
        warning_days=int(filter_warning)
    )
    upcoming = get_upcoming_expirations()
    past_due = get_past_due_licenses()
    
    # Categorize upcoming expirations
    critical = []
    warning = []
    normal = []
    
    for license in upcoming:
        days_until = license.get('days_until_expiration', 0)
        if days_until <= int(filter_critical): # Use filter_critical for critical
            critical.append(license)
        elif days_until <= int(filter_warning): # Use filter_warning for warning
            warning.append(license)
        else:
            normal.append(license)
    
    return render_template('dashboard.html', 
                         stats=stats,
                         critical=critical,
                         warning=warning,
                         normal=normal,
                         past_due=past_due,
                         filter_upcoming=filter_upcoming,
                         filter_critical=filter_critical,
                         filter_warning=filter_warning)

@app.route('/licenses')
def licenses():
    """All licenses page with optional filtering"""
    filter_type = request.args.get('filter', None)
    
    # Get custom filter parameters, with defaults
    upcoming_days = int(request.args.get('upcoming_days', 35))
    critical_days = int(request.args.get('critical_days', 10))
    warning_days = int(request.args.get('warning_days', 30))
    
    all_licenses = get_all_licenses()
    
    # Apply filtering based on the filter parameter
    if filter_type == 'critical':
        # Show licenses expiring in next critical_days
        from datetime import datetime, timedelta
        cutoff_date = (datetime.now() + timedelta(days=critical_days)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        filtered_licenses = [
            license for license in all_licenses 
            if license.get('expiration_date') and license['expiration_date'] <= cutoff_date and license['expiration_date'] >= today
        ]
        page_title = f"Critical Licenses (Expiring in {critical_days} Days)"
    elif filter_type == 'warning':
        # Show licenses expiring in next warning_days (but not critical)
        from datetime import datetime, timedelta
        cutoff_date_warning = (datetime.now() + timedelta(days=warning_days)).strftime('%Y-%m-%d')
        cutoff_date_critical = (datetime.now() + timedelta(days=critical_days)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        filtered_licenses = [
            license for license in all_licenses 
            if license.get('expiration_date') and license['expiration_date'] <= cutoff_date_warning and license['expiration_date'] > cutoff_date_critical and license['expiration_date'] >= today
        ]
        page_title = f"Warning Licenses (Expiring in {critical_days+1}-{warning_days} Days)"
    elif filter_type == 'upcoming':
        # Show licenses expiring in next upcoming_days
        from datetime import datetime, timedelta
        cutoff_date = (datetime.now() + timedelta(days=upcoming_days)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        filtered_licenses = [
            license for license in all_licenses 
            if license.get('expiration_date') and license['expiration_date'] <= cutoff_date and license['expiration_date'] >= today
        ]
        page_title = f"Upcoming Expirations (Next {upcoming_days} Days)"
    elif filter_type == 'past_due':
        # Show past due licenses
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        filtered_licenses = [
            license for license in all_licenses 
            if license.get('expiration_date') and license['expiration_date'] < today
        ]
        # Add days overdue calculation
        for license in filtered_licenses:
            if license.get('expiration_date'):
                exp_date = datetime.strptime(license['expiration_date'], '%Y-%m-%d')
                days_overdue = (datetime.now() - exp_date).days
                license['days_overdue'] = days_overdue
        page_title = "Past Due Licenses (Expired)"
    else:
        filtered_licenses = all_licenses
        page_title = "All Licenses"
    
    return render_template('licenses.html', 
                         licenses=filtered_licenses, 
                         filter_type=filter_type,
                         page_title=page_title,
                         upcoming_days=upcoming_days,
                         critical_days=critical_days,
                         warning_days=warning_days)

@app.route('/reminders')
def reminders():
    """Reminder history page"""
    sent_reminders = get_sent_reminders()
    return render_template('reminders.html', reminders=sent_reminders)

@app.route('/api/upcoming')
def api_upcoming():
    """API endpoint for upcoming expirations"""
    upcoming = get_upcoming_expirations()
    return jsonify(upcoming)

@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics"""
    stats = get_license_statistics()
    return jsonify(stats)

@app.route('/api/license/<int:license_id>')
def api_license_detail(license_id):
    """API endpoint for license details"""
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500
    try:
        result = supabase.table('licenses').select('*').eq('id', license_id).execute()
        if result.data:
            return jsonify(result.data[0])
        else:
            return jsonify({'error': 'License not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/license/<int:license_id>', methods=['PUT'])
def api_update_license(license_id):
    """API endpoint to update license information"""
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['lic_name', 'lic_type', 'lic_state']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Update the license
        result = supabase.table('licenses').update(data).eq('id', license_id).execute()
        
        if result.data:
            return jsonify({'success': True, 'message': 'License updated successfully', 'data': result.data[0]})
        else:
            return jsonify({'error': 'License not found or update failed'}), 404
            
    except Exception as e:
        logger.error(f"Error updating license {license_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/license', methods=['POST'])
def api_create_license():
    """API endpoint to create a new license"""
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['lic_name', 'lic_type', 'lic_state']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Remove id from data if it exists (let the database auto-generate it)
        if 'id' in data:
            del data['id']
        
        # Create the license
        result = supabase.table('licenses').insert(data).execute()
        
        if result.data:
            return jsonify({'success': True, 'message': 'License created successfully', 'data': result.data[0]})
        else:
            return jsonify({'error': 'Failed to create license'}), 400
            
    except Exception as e:
        logger.error(f"Error creating license: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/license/<int:license_id>', methods=['DELETE'])
def api_delete_license(license_id):
    """API endpoint to delete a license"""
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500
    try:
        # Delete the license
        result = supabase.table('licenses').delete().eq('id', license_id).execute()
        
        if result.data:
            return jsonify({'success': True, 'message': 'License deleted successfully'})
        else:
            return jsonify({'error': 'License not found or delete failed'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting license {license_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/license-types')
def api_license_types():
    """API endpoint to get distinct license types"""
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500
    try:
        result = supabase.table('licenses').select('lic_type').execute()
        
        # Get unique types, filter out None/empty values
        types = set()
        for item in result.data:
            if item.get('lic_type') and item['lic_type'].strip():
                types.add(item['lic_type'].strip())
        
        return jsonify({'types': sorted(list(types))})
        
    except Exception as e:
        logger.error(f"Error fetching license types: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/license/<int:license_id>/toggle-emails', methods=['POST'])
def api_toggle_license_emails(license_id):
    """API endpoint to toggle email notifications for a license"""
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500
    try:
        # Get current email_enabled status
        result = supabase.table('licenses').select('email_enabled, lic_name').eq('id', license_id).execute()
        
        if not result.data:
            return jsonify({'error': 'License not found'}), 404
        
        current_status = result.data[0].get('email_enabled', True)
        license_name = result.data[0].get('lic_name', 'Unknown')
        new_status = not current_status
        
        # Update the email_enabled status
        update_result = supabase.table('licenses').update({
            'email_enabled': new_status
        }).eq('id', license_id).execute()
        
        if update_result.data:
            action = "enabled" if new_status else "disabled"
            return jsonify({
                'success': True, 
                'message': f'Email notifications {action} for {license_name}',
                'email_enabled': new_status,
                'license_name': license_name
            })
        else:
            return jsonify({'error': 'Failed to update email status'}), 400
            
    except Exception as e:
        logger.error(f"Error toggling email status for license {license_id}: {e}")
        return jsonify({'error': str(e)}), 500

# Export the Flask app for Vercel
# This is the key - Vercel looks for an 'app' variable
# No need for a custom handler function

# For local development
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting License Dashboard on http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    
    app.run(host='0.0.0.0', port=port, debug=debug) 