from flask import Flask
from .config.config import config
import logging
import os
from logging.handlers import RotatingFileHandler
import sys

def setup_logging(app):
    """Configure the logging system for the application."""
    log_dir = app.config['LOG_DIR']
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger('diamond_app')
    logger.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # File handler
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'diamond_app.log'),
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Error file handler
    error_file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=10485760,
        backupCount=10
    )
    error_file_handler.setLevel(logging.ERROR)
    
    # Formatters
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    console_handler.setFormatter(console_formatter)
    file_handler.setFormatter(file_formatter)
    error_file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_file_handler)
    
    return logger

def create_app(config_name='default'):
    """Application factory function."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Ensure required directories exist
    os.makedirs(app.config['DATA_DIR'], exist_ok=True)
    os.makedirs(app.config['BACKUP_DIR'], exist_ok=True)
    os.makedirs(app.config['LOG_DIR'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Setup logging
    logger = setup_logging(app)
    logger.info(f"Starting Diamond Accounting Application in {config_name} mode")
    
    # Register blueprints
    from .routes import (
        main_bp,
        inventory_bp,
        sales_bp,
        purchases_bp,
        reports_bp,
        debug_bp
    )
    
    app.register_blueprint(main_bp)
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(sales_bp, url_prefix='/sales')
    app.register_blueprint(purchases_bp, url_prefix='/purchases')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    
    if app.debug:
        app.register_blueprint(debug_bp, url_prefix='/debug')
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def register_error_handlers(app):
    """Register error handlers for the application."""
    
    @app.errorhandler(404)
    def page_not_found(e):
        logger = logging.getLogger('diamond_app')
        logger.info(f"404 error: {request.path}")
        return render_template('error.html', 
                             error_code=404, 
                             error_message="The page you're looking for doesn't exist."), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        logger = logging.getLogger('diamond_app')
        logger.error(f"500 error: {str(e)}")
        logger.error(f"Request: {request.path} {request.method}")
        logger.error(f"Form data: {request.form}")
        return render_template('error.html', 
                             error_code=500, 
                             error_message="Something went wrong on our end. Please try again later."), 500 