from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from ..services.data import (
    validate_data_consistency,
    fix_data_inconsistencies,
    fix_data_types,
    validate_excel_files
)
import logging
import os
import time
import psutil

bp = Blueprint('debug', __name__)
logger = logging.getLogger('diamond_app')

@bp.before_request
def check_debug_mode():
    """Ensure debug routes are only accessible in debug mode."""
    if not current_app.debug:
        flash('Debug routes are only available in debug mode', 'error')
        return redirect(url_for('main.index'))

@bp.route('/validate_data')
def validate_data():
    """Data validation tool for checking data consistency."""
    try:
        # Check data consistency
        inconsistencies = validate_data_consistency()
        
        # Check Excel files
        excel_issues = validate_excel_files()
        
        return render_template('debug/debug_validate.html',
                             inconsistencies=inconsistencies,
                             excel_issues=excel_issues)
    except Exception as e:
        logger.error(f"Error in data validation: {str(e)}")
        flash('Error validating data', 'error')
        return redirect(url_for('main.index'))

@bp.route('/fix_data', methods=['POST'])
def fix_data():
    """Fix data inconsistencies and type issues."""
    try:
        # Fix data inconsistencies
        fixed_inconsistencies = fix_data_inconsistencies()
        
        # Fix data types
        fixed_types = fix_data_types()
        
        response = {
            'fixed_inconsistencies': fixed_inconsistencies,
            'fixed_types': fixed_types,
            'success': True
        }
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error fixing data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/responsive')
def responsive_test():
    """Responsive design testing tool."""
    try:
        return render_template('debug/debug_responsive.html')
    except Exception as e:
        logger.error(f"Error loading responsive testing tool: {str(e)}")
        flash('Error loading responsive testing tool', 'error')
        return redirect(url_for('main.index'))

@bp.route('/logs')
def view_logs():
    """View application logs."""
    try:
        # Read the last 1000 lines of the main log file
        log_file = os.path.join(current_app.config['LOG_DIR'], 'diamond_app.log')
        with open(log_file, 'r') as f:
            logs = f.readlines()[-1000:]
        
        # Read the last 1000 lines of the error log file
        error_log_file = os.path.join(current_app.config['LOG_DIR'], 'error.log')
        with open(error_log_file, 'r') as f:
            error_logs = f.readlines()[-1000:]
        
        return render_template('debug/logs.html',
                             logs=logs,
                             error_logs=error_logs)
    except Exception as e:
        logger.error(f"Error viewing logs: {str(e)}")
        flash('Error viewing logs', 'error')
        return redirect(url_for('main.index'))

@bp.route('/performance')
def performance_metrics():
    """View performance metrics."""
    try:
        # Get system metrics
        metrics = {
            'memory_usage': psutil.Process().memory_info().rss / 1024 / 1024,  # MB
            'cpu_percent': psutil.Process().cpu_percent(),
            'open_files': len(psutil.Process().open_files()),
            'threads': psutil.Process().num_threads(),
            'connections': len(psutil.Process().connections()),
            'uptime': time.time() - psutil.Process().create_time()
        }
        
        return render_template('debug/performance.html', metrics=metrics)
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        flash('Error getting performance metrics', 'error')
        return redirect(url_for('main.index'))

@bp.route('/config')
def view_config():
    """View application configuration."""
    try:
        # Get configuration, excluding sensitive values
        config = {
            key: value for key, value in current_app.config.items()
            if not key.startswith('_') and 'SECRET' not in key and 'KEY' not in key
        }
        
        return render_template('debug/config.html', config=config)
    except Exception as e:
        logger.error(f"Error viewing configuration: {str(e)}")
        flash('Error viewing configuration', 'error')
        return redirect(url_for('main.index')) 