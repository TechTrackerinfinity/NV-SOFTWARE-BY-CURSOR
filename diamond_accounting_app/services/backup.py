import os
import zipfile
import tempfile
import shutil
from datetime import datetime
import logging
import traceback
import sys
from flask import current_app

logger = logging.getLogger('diamond_app')

__all__ = ['create_backup', 'restore_from_backup']

def create_backup():
    """
    Create a backup of all data files in a zip file.
    Returns the path to the created backup file.
    """
    try:
        logger.info("Creating backup of all data files")
        
        data_dir = current_app.config['DATA_DIR']
        backup_dir = current_app.config['BACKUP_DIR']
        
        # List of files to backup
        data_files = [
            'purchases.xlsx',
            'sales.xlsx',
            'payments.xlsx',
            'inventory.xlsx',
            'rough_inventory.xlsx'
        ]
        
        # Create a timestamp for the backup file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'diamond_data_backup_{timestamp}.zip')
        logger.debug(f"Backup file path: {backup_file}")
        
        # Check if all required files exist
        missing_files = []
        for file_name in data_files:
            file_path = os.path.join(data_dir, file_name)
            if not os.path.exists(file_path):
                missing_files.append(file_name)
        
        if missing_files:
            logger.warning(f"The following files are missing and will not be included in the backup: {', '.join(missing_files)}")
        
        # Create a zip file containing all data files
        with zipfile.ZipFile(backup_file, 'w') as zipf:
            for file_name in data_files:
                file_path = os.path.join(data_dir, file_name)
                if os.path.exists(file_path):
                    zipf.write(file_path, file_name)
                    logger.debug(f"Added file to backup: {file_name}")
        
        # Keep only the 10 most recent backups
        backup_files = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir) 
                              if f.startswith('diamond_data_backup_') and f.endswith('.zip')],
                             key=os.path.getmtime, reverse=True)
        
        for old_backup in backup_files[10:]:
            try:
                os.remove(old_backup)
                logger.debug(f"Removed old backup: {os.path.basename(old_backup)}")
            except Exception as e:
                logger.warning(f"Could not remove old backup {old_backup}: {str(e)}")
        
        logger.info(f"Backup created successfully: {os.path.basename(backup_file)}")
        return backup_file
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        # Log the traceback
        exc_info = sys.exc_info()
        tb_lines = traceback.format_exception(*exc_info)
        tb_text = ''.join(tb_lines)
        logger.error(f"Traceback: {tb_text}")
        return None

def restore_from_backup(backup_file):
    """
    Restore data from a backup zip file.
    """
    try:
        logger.info(f"Restoring from backup: {os.path.basename(backup_file)}")
        
        data_dir = current_app.config['DATA_DIR']
        backup_dir = current_app.config['BACKUP_DIR']
        
        # Validate the backup file
        if not os.path.exists(backup_file):
            logger.error(f"Backup file does not exist: {backup_file}")
            return False
            
        # Verify it's a valid zip file
        try:
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                # Check if the zip file contains the expected files
                file_list = zipf.namelist()
                logger.debug(f"Files in backup: {', '.join(file_list)}")
                
                expected_files = ['purchases.xlsx', 'sales.xlsx', 'payments.xlsx', 
                                'inventory.xlsx', 'rough_inventory.xlsx']
                missing_files = [f for f in expected_files if f not in file_list]
                
                if missing_files:
                    logger.warning(f"The following files are missing from the backup: {', '.join(missing_files)}")
                    # Proceed anyway, but warn the user
        except zipfile.BadZipFile:
            logger.error(f"{backup_file} is not a valid zip file")
            return False
            
        # Create backup of current data before restoring
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pre_restore_backup = os.path.join(backup_dir, f'pre_restore_backup_{timestamp}.zip')
        try:
            with zipfile.ZipFile(pre_restore_backup, 'w') as zipf:
                for file_name in ['purchases.xlsx', 'sales.xlsx', 'payments.xlsx', 
                                'inventory.xlsx', 'rough_inventory.xlsx']:
                    file_path = os.path.join(data_dir, file_name)
                    if os.path.exists(file_path):
                        zipf.write(file_path, file_name)
            logger.info(f"Created pre-restore backup: {os.path.basename(pre_restore_backup)}")
        except Exception as e:
            logger.warning(f"Could not create pre-restore backup: {str(e)}")
            # Continue with restore even if pre-restore backup fails
        
        # Create a temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.debug(f"Created temporary directory for extraction: {temp_dir}")
            
            # Extract the backup file
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(temp_dir)
                logger.debug(f"Extracted backup to temporary directory")
            
            # Copy the extracted files to the data directory
            for file_name in os.listdir(temp_dir):
                src_path = os.path.join(temp_dir, file_name)
                dst_path = os.path.join(data_dir, file_name)
                shutil.copy2(src_path, dst_path)
                logger.debug(f"Copied {file_name} to data directory")
        
        # Validate the restored data
        try:
            logger.info("Validating restored data")
            from ..services.data import fix_data_types, validate_data_consistency
            fix_data_types()
            validate_data_consistency()
            logger.info("Data validation successful after restore")
        except Exception as e:
            logger.warning(f"Data validation after restore encountered issues: {str(e)}")
            # Continue anyway, the data might still be usable
        
        logger.info("Restore completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error restoring from backup: {str(e)}")
        # Log the traceback
        exc_info = sys.exc_info()
        tb_lines = traceback.format_exception(*exc_info)
        tb_text = ''.join(tb_lines)
        logger.error(f"Traceback: {tb_text}")
        return False 