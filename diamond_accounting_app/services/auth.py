from functools import wraps
from flask import session, redirect, url_for, flash
import logging

logger = logging.getLogger('diamond_app')

__all__ = ['login_required', 'login_user', 'logout_user']

def login_required(f):
    """Decorator to require login for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

def login_user(user_id):
    """Log in a user by setting their ID in the session."""
    session['user_id'] = user_id
    logger.info(f"User {user_id} logged in")

def logout_user():
    """Log out the current user."""
    user_id = session.pop('user_id', None)
    if user_id:
        logger.info(f"User {user_id} logged out")
    session.clear() 