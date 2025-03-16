from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..services.auth import login_required
import logging

bp = Blueprint('main', __name__)
logger = logging.getLogger('diamond_app')

@bp.route('/')
@login_required
def index():
    """Main dashboard page."""
    logger.info("Accessing dashboard")
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering dashboard: {str(e)}")
        flash("Error loading dashboard", "error")
        return redirect(url_for('main.error'))

@bp.route('/error')
def error():
    """Generic error page."""
    return render_template('error.html') 