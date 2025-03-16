from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from ..services.backup import (
    create_backup,
    restore_from_backup,
    get_backup_list,
    delete_backup,
    validate_backup_file
)
import logging
import os
from datetime import datetime

bp = Blueprint('backup', __name__)
logger = logging.getLogger('diamond_app')

@bp.route('/backup', methods=['GET', 'POST'])
def backup():
    """Handle backup creation and restoration."""
    try:
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'create':
                # Create a new backup
                backup_file = create_backup()
                if backup_file:
                    flash(f'Backup created successfully: {os.path.basename(backup_file)}', 'success')
                else:
                    flash('Failed to create backup', 'error')
            
            elif action == 'restore':
                # Restore from selected backup
                backup_file = request.form.get('backup_file')
                if not backup_file:
                    flash('No backup file selected', 'error')
                else:
                    # Validate backup file before restoring
                    if validate_backup_file(backup_file):
                        if restore_from_backup(backup_file):
                            flash('Data restored successfully from backup', 'success')
                        else:
                            flash('Failed to restore from backup', 'error')
                    else:
                        flash('Invalid or corrupted backup file', 'error')
            
            elif action == 'delete':
                # Delete selected backup
                backup_file = request.form.get('backup_file')
                if not backup_file:
                    flash('No backup file selected', 'error')
                else:
                    if delete_backup(backup_file):
                        flash('Backup deleted successfully', 'success')
                    else:
                        flash('Failed to delete backup', 'error')
        
        # Get list of available backups
        backups = get_backup_list()
        
        # Format backup information
        backup_info = []
        for backup in backups:
            # Get backup file stats
            stats = os.stat(os.path.join(current_app.config['BACKUP_DIR'], backup))
            
            # Format creation time
            created = datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
            
            # Format file size
            size_mb = stats.st_size / (1024 * 1024)  # Convert to MB
            
            backup_info.append({
                'filename': backup,
                'created': created,
                'size': f'{size_mb:.2f} MB'
            })
        
        return render_template('backup/backup.html',
                             backups=backup_info)
    
    except Exception as e:
        logger.error(f"Error in backup route: {str(e)}")
        flash('Error processing backup operation', 'error')
        return redirect(url_for('main.index'))

@bp.route('/download_backup/<filename>')
def download_backup(filename):
    """Download a backup file."""
    try:
        backup_path = os.path.join(current_app.config['BACKUP_DIR'], filename)
        if os.path.exists(backup_path):
            return send_file(backup_path,
                           mimetype='application/zip',
                           as_attachment=True,
                           download_name=filename)
        else:
            flash('Backup file not found', 'error')
            return redirect(url_for('backup.backup'))
    except Exception as e:
        logger.error(f"Error downloading backup: {str(e)}")
        flash('Error downloading backup', 'error')
        return redirect(url_for('backup.backup'))

@bp.route('/upload_backup', methods=['POST'])
def upload_backup():
    """Upload a backup file."""
    try:
        if 'file' not in request.files:
            flash('No file provided', 'error')
            return redirect(url_for('backup.backup'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('backup.backup'))
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        backup_path = os.path.join(current_app.config['BACKUP_DIR'], filename)
        file.save(backup_path)
        
        # Validate the uploaded backup
        if validate_backup_file(filename):
            flash('Backup file uploaded successfully', 'success')
        else:
            # Delete invalid backup file
            os.remove(backup_path)
            flash('Invalid backup file', 'error')
        
        return redirect(url_for('backup.backup'))
    except Exception as e:
        logger.error(f"Error uploading backup: {str(e)}")
        flash('Error uploading backup', 'error')
        return redirect(url_for('backup.backup'))

@bp.route('/validate_backup/<filename>')
def validate_backup(filename):
    """Validate a backup file."""
    try:
        is_valid = validate_backup_file(filename)
        return jsonify({
            'valid': is_valid,
            'message': 'Backup file is valid' if is_valid else 'Invalid or corrupted backup file'
        })
    except Exception as e:
        logger.error(f"Error validating backup: {str(e)}")
        return jsonify({
            'valid': False,
            'message': f'Error validating backup: {str(e)}'
        }), 500 