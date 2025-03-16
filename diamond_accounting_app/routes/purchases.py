from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from ..services.purchases import (
    get_purchase_records,
    add_purchase_record,
    get_purchase_details,
    update_purchase_record,
    delete_purchase_record
)
import logging

bp = Blueprint('purchases', __name__)
logger = logging.getLogger('diamond_app')

@bp.route('/buy', methods=['GET', 'POST'])
def buy():
    """Handle the purchase of rough diamonds."""
    try:
        if request.method == 'POST':
            data = request.form.to_dict()
            if add_purchase_record(data):
                flash('Purchase record added successfully', 'success')
            else:
                flash('Failed to add purchase record', 'error')
            return redirect(url_for('purchases.records'))
        
        # For GET request, show the purchase form
        return render_template('purchases/buy.html')
    except Exception as e:
        logger.error(f"Error in buy route: {str(e)}")
        flash('Error processing purchase', 'error')
        return redirect(url_for('main.index'))

@bp.route('/purchase_records')
def records():
    """Display all purchase records."""
    try:
        purchases = get_purchase_records()
        return render_template('purchases/records.html', purchases=purchases)
    except Exception as e:
        logger.error(f"Error loading purchase records: {str(e)}")
        flash('Error loading purchase records', 'error')
        return redirect(url_for('main.index'))

@bp.route('/purchase_details/<purchase_id>')
def purchase_details(purchase_id):
    """Get details of a specific purchase."""
    try:
        purchase = get_purchase_details(purchase_id)
        if purchase:
            return jsonify(purchase)
        return jsonify({'error': 'Purchase not found'}), 404
    except Exception as e:
        logger.error(f"Error getting purchase details: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/edit_purchase/<purchase_id>', methods=['GET', 'POST'])
def edit_purchase(purchase_id):
    """Edit a purchase record."""
    try:
        if request.method == 'POST':
            data = request.form.to_dict()
            if update_purchase_record(purchase_id, data):
                flash('Purchase record updated successfully', 'success')
            else:
                flash('Failed to update purchase record', 'error')
            return redirect(url_for('purchases.records'))
        
        purchase = get_purchase_details(purchase_id)
        if purchase:
            return render_template('purchases/edit_purchase.html', purchase=purchase)
        flash('Purchase not found', 'error')
        return redirect(url_for('purchases.records'))
    except Exception as e:
        logger.error(f"Error editing purchase record: {str(e)}")
        flash('Error editing purchase record', 'error')
        return redirect(url_for('purchases.records'))

@bp.route('/delete_purchase', methods=['POST'])
def delete_purchase():
    """Delete a purchase record."""
    try:
        purchase_id = request.form.get('purchase_id')
        if delete_purchase_record(purchase_id):
            flash('Purchase record deleted successfully', 'success')
        else:
            flash('Failed to delete purchase record', 'error')
        return redirect(url_for('purchases.records'))
    except Exception as e:
        logger.error(f"Error deleting purchase record: {str(e)}")
        flash('Error deleting purchase record', 'error')
        return redirect(url_for('purchases.records')) 