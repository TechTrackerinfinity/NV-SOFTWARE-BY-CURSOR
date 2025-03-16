from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from ..services.auth import login_user, logout_user, login_required
from ..services.dashboard import get_dashboard_data
import logging

bp = Blueprint('main', __name__)
logger = logging.getLogger('diamond_app')

@bp.route('/')
@login_required
def index():
    """Main dashboard page."""
    try:
        dashboard_data = get_dashboard_data()
        return render_template('main/dashboard.html', data=dashboard_data)
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        flash('Error loading dashboard', 'error')
        return render_template('main/error.html', error=str(e))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            if login_user(username, password):
                flash('Login successful', 'success')
                return redirect(url_for('main.index'))
            else:
                flash('Invalid username or password', 'error')
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            flash('Error during login', 'error')
    
    return render_template('main/login.html')

@bp.route('/logout')
def logout():
    """Handle user logout."""
    try:
        logout_user()
        flash('Logged out successfully', 'success')
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        flash('Error during logout', 'error')
    
    return redirect(url_for('main.login'))

@bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    try:
        return render_template('main/profile.html')
    except Exception as e:
        logger.error(f"Error loading profile: {str(e)}")
        flash('Error loading profile', 'error')
        return redirect(url_for('main.index'))

@bp.route('/settings')
@login_required
def settings():
    """Application settings page."""
    try:
        return render_template('main/settings.html')
    except Exception as e:
        logger.error(f"Error loading settings: {str(e)}")
        flash('Error loading settings', 'error')
        return redirect(url_for('main.index'))

@bp.app_errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    logger.info(f"404 error: {request.path}")
    return render_template('main/error.html',
                         error_code=404,
                         error_message="The page you're looking for doesn't exist."), 404

@bp.app_errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"500 error: {str(error)}")
    return render_template('main/error.html',
                         error_code=500,
                         error_message="An internal error occurred."), 500 