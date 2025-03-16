from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from ..services.inventory import (
    get_inventory_items,
    add_inventory_item,
    get_inventory_item_details,
    update_inventory_item,
    delete_inventory_item,
    upload_inventory_data,
    get_rough_inventory_items,
    add_rough_inventory_item,
    get_rough_inventory_item_details,
    update_rough_inventory_item,
    delete_rough_inventory_item,
    upload_rough_inventory_data
)
from ..services.data import enhance_excel_formatting
import logging
import os
import pandas as pd
from werkzeug.utils import secure_filename

bp = Blueprint('inventory', __name__)
logger = logging.getLogger('diamond_app')

@bp.route('/inventory')
def inventory():
    """Display the inventory page."""
    try:
        items = get_inventory_items()
        return render_template('inventory/inventory.html', items=items)
    except Exception as e:
        logger.error(f"Error in inventory route: {str(e)}")
        flash('Error loading inventory', 'error')
        return redirect(url_for('main.index'))

@bp.route('/add_inventory_item', methods=['POST'])
def add_item():
    """Add a new inventory item."""
    try:
        data = request.form.to_dict()
        if add_inventory_item(data):
            flash('Inventory item added successfully', 'success')
        else:
            flash('Failed to add inventory item', 'error')
        return redirect(url_for('inventory.inventory'))
    except Exception as e:
        logger.error(f"Error adding inventory item: {str(e)}")
        flash('Error adding inventory item', 'error')
        return redirect(url_for('inventory.inventory'))

@bp.route('/inventory_item_details/<item_id>')
def item_details(item_id):
    """Get details of a specific inventory item."""
    try:
        item = get_inventory_item_details(item_id)
        if item:
            return jsonify(item)
        return jsonify({'error': 'Item not found'}), 404
    except Exception as e:
        logger.error(f"Error getting inventory item details: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/edit_inventory_item/<item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    """Edit an inventory item."""
    try:
        if request.method == 'POST':
            data = request.form.to_dict()
            if update_inventory_item(item_id, data):
                flash('Inventory item updated successfully', 'success')
            else:
                flash('Failed to update inventory item', 'error')
            return redirect(url_for('inventory.inventory'))
        
        item = get_inventory_item_details(item_id)
        if item:
            return render_template('inventory/edit_item.html', item=item)
        flash('Item not found', 'error')
        return redirect(url_for('inventory.inventory'))
    except Exception as e:
        logger.error(f"Error editing inventory item: {str(e)}")
        flash('Error editing inventory item', 'error')
        return redirect(url_for('inventory.inventory'))

@bp.route('/delete_inventory_item', methods=['POST'])
def delete_item():
    """Delete an inventory item."""
    try:
        item_id = request.form.get('item_id')
        if delete_inventory_item(item_id):
            flash('Inventory item deleted successfully', 'success')
        else:
            flash('Failed to delete inventory item', 'error')
        return redirect(url_for('inventory.inventory'))
    except Exception as e:
        logger.error(f"Error deleting inventory item: {str(e)}")
        flash('Error deleting inventory item', 'error')
        return redirect(url_for('inventory.inventory'))

@bp.route('/upload_inventory', methods=['POST'])
def upload_inventory():
    """Upload inventory data from Excel file."""
    try:
        if 'file' not in request.files:
            flash('No file provided', 'error')
            return redirect(url_for('inventory.inventory'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('inventory.inventory'))
        
        if upload_inventory_data(file):
            flash('Inventory data uploaded successfully', 'success')
        else:
            flash('Failed to upload inventory data', 'error')
        return redirect(url_for('inventory.inventory'))
    except Exception as e:
        logger.error(f"Error uploading inventory data: {str(e)}")
        flash('Error uploading inventory data', 'error')
        return redirect(url_for('inventory.inventory'))

@bp.route('/download_inventory_template')
def download_template():
    """Download inventory Excel template."""
    try:
        template_data = {
            'item_id': [],
            'carats': [],
            'clarity': [],
            'color': [],
            'cut': [],
            'price': []
        }
        df = pd.DataFrame(template_data)
        
        # Create a temporary file
        temp_file = os.path.join(current_app.config['UPLOAD_FOLDER'], 'inventory_template.xlsx')
        df.to_excel(temp_file, index=False)
        
        # Enhance the formatting
        enhance_excel_formatting(temp_file)
        
        return send_file(temp_file,
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        as_attachment=True,
                        download_name='inventory_template.xlsx')
    except Exception as e:
        logger.error(f"Error creating inventory template: {str(e)}")
        flash('Error creating template', 'error')
        return redirect(url_for('inventory.inventory'))

# Rough Inventory Routes
@bp.route('/rough_inventory')
def rough_inventory():
    """Display the rough inventory page."""
    try:
        items = get_rough_inventory_items()
        return render_template('inventory/rough_inventory.html', items=items)
    except Exception as e:
        logger.error(f"Error in rough inventory route: {str(e)}")
        flash('Error loading rough inventory', 'error')
        return redirect(url_for('main.index'))

@bp.route('/add_rough_inventory_item', methods=['POST'])
def add_rough_item():
    """Add a new rough inventory item."""
    try:
        data = request.form.to_dict()
        if add_rough_inventory_item(data):
            flash('Rough inventory item added successfully', 'success')
        else:
            flash('Failed to add rough inventory item', 'error')
        return redirect(url_for('inventory.rough_inventory'))
    except Exception as e:
        logger.error(f"Error adding rough inventory item: {str(e)}")
        flash('Error adding rough inventory item', 'error')
        return redirect(url_for('inventory.rough_inventory'))

@bp.route('/rough_inventory_item_details/<item_id>')
def rough_item_details(item_id):
    """Get details of a specific rough inventory item."""
    try:
        item = get_rough_inventory_item_details(item_id)
        if item:
            return jsonify(item)
        return jsonify({'error': 'Item not found'}), 404
    except Exception as e:
        logger.error(f"Error getting rough inventory item details: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/edit_rough_inventory_item/<item_id>', methods=['GET', 'POST'])
def edit_rough_item(item_id):
    """Edit a rough inventory item."""
    try:
        if request.method == 'POST':
            data = request.form.to_dict()
            if update_rough_inventory_item(item_id, data):
                flash('Rough inventory item updated successfully', 'success')
            else:
                flash('Failed to update rough inventory item', 'error')
            return redirect(url_for('inventory.rough_inventory'))
        
        item = get_rough_inventory_item_details(item_id)
        if item:
            return render_template('inventory/edit_rough_item.html', item=item)
        flash('Item not found', 'error')
        return redirect(url_for('inventory.rough_inventory'))
    except Exception as e:
        logger.error(f"Error editing rough inventory item: {str(e)}")
        flash('Error editing rough inventory item', 'error')
        return redirect(url_for('inventory.rough_inventory'))

@bp.route('/delete_rough_inventory_item', methods=['POST'])
def delete_rough_item():
    """Delete a rough inventory item."""
    try:
        item_id = request.form.get('item_id')
        if delete_rough_inventory_item(item_id):
            flash('Rough inventory item deleted successfully', 'success')
        else:
            flash('Failed to delete rough inventory item', 'error')
        return redirect(url_for('inventory.rough_inventory'))
    except Exception as e:
        logger.error(f"Error deleting rough inventory item: {str(e)}")
        flash('Error deleting rough inventory item', 'error')
        return redirect(url_for('inventory.rough_inventory'))

@bp.route('/upload_rough_inventory', methods=['POST'])
def upload_rough_inventory():
    """Upload rough inventory data from Excel file."""
    try:
        if 'file' not in request.files:
            flash('No file provided', 'error')
            return redirect(url_for('inventory.rough_inventory'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('inventory.rough_inventory'))
        
        if upload_rough_inventory_data(file):
            flash('Rough inventory data uploaded successfully', 'success')
        else:
            flash('Failed to upload rough inventory data', 'error')
        return redirect(url_for('inventory.rough_inventory'))
    except Exception as e:
        logger.error(f"Error uploading rough inventory data: {str(e)}")
        flash('Error uploading rough inventory data', 'error')
        return redirect(url_for('inventory.rough_inventory'))

@bp.route('/download_rough_inventory_template')
def download_rough_template():
    """Download rough inventory Excel template."""
    try:
        template_data = {
            'rough_id': [],
            'kapan_no': [],
            'shape_category': [],
            'weight': [],
            'pieces': [],
            'purchase_price': []
        }
        df = pd.DataFrame(template_data)
        
        # Create a temporary file
        temp_file = os.path.join(current_app.config['UPLOAD_FOLDER'], 'rough_inventory_template.xlsx')
        df.to_excel(temp_file, index=False)
        
        # Enhance the formatting
        enhance_excel_formatting(temp_file)
        
        return send_file(temp_file,
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        as_attachment=True,
                        download_name='rough_inventory_template.xlsx')
    except Exception as e:
        logger.error(f"Error creating rough inventory template: {str(e)}")
        flash('Error creating template', 'error')
        return redirect(url_for('inventory.rough_inventory')) 