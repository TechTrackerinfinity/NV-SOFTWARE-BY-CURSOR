from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from ..services.sales import (
    get_sales_records,
    add_sale_record,
    get_sale_details,
    update_sale_record,
    delete_sale_record,
    get_payment_records,
    add_payment_record,
    get_payment_details,
    update_payment_record
)
from ..services.inventory import get_inventory_items
import logging

bp = Blueprint('sales', __name__)
logger = logging.getLogger('diamond_app')

@bp.route('/sell', methods=['GET', 'POST'])
def sell():
    """Handle the sale of inventory items."""
    try:
        if request.method == 'POST':
            data = request.form.to_dict()
            if add_sale_record(data):
                flash('Sale record added successfully', 'success')
            else:
                flash('Failed to add sale record', 'error')
            return redirect(url_for('sales.records'))
        
        # For GET request, show the sale form with available inventory
        inventory_items = get_inventory_items()
        return render_template('sales/sell.html', inventory_items=inventory_items)
    except Exception as e:
        logger.error(f"Error in sell route: {str(e)}")
        flash('Error processing sale', 'error')
        return redirect(url_for('main.index'))

@bp.route('/records')
def records():
    """Display all sales records."""
    try:
        sales = get_sales_records()
        return render_template('sales/records.html', sales=sales)
    except Exception as e:
        logger.error(f"Error loading sales records: {str(e)}")
        flash('Error loading sales records', 'error')
        return redirect(url_for('main.index'))

@bp.route('/sale_details/<sale_id>')
def sale_details(sale_id):
    """Get details of a specific sale."""
    try:
        sale = get_sale_details(sale_id)
        if sale:
            return jsonify(sale)
        return jsonify({'error': 'Sale not found'}), 404
    except Exception as e:
        logger.error(f"Error getting sale details: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/edit_sale/<sale_id>', methods=['GET', 'POST'])
def edit_sale(sale_id):
    """Edit a sale record."""
    try:
        if request.method == 'POST':
            data = request.form.to_dict()
            if update_sale_record(sale_id, data):
                flash('Sale record updated successfully', 'success')
            else:
                flash('Failed to update sale record', 'error')
            return redirect(url_for('sales.records'))
        
        sale = get_sale_details(sale_id)
        if sale:
            inventory_items = get_inventory_items()
            return render_template('sales/edit_sale.html', sale=sale, inventory_items=inventory_items)
        flash('Sale not found', 'error')
        return redirect(url_for('sales.records'))
    except Exception as e:
        logger.error(f"Error editing sale record: {str(e)}")
        flash('Error editing sale record', 'error')
        return redirect(url_for('sales.records'))

@bp.route('/delete_sale', methods=['POST'])
def delete_sale():
    """Delete a sale record."""
    try:
        sale_id = request.form.get('sale_id')
        if delete_sale_record(sale_id):
            flash('Sale record deleted successfully', 'success')
        else:
            flash('Failed to delete sale record', 'error')
        return redirect(url_for('sales.records'))
    except Exception as e:
        logger.error(f"Error deleting sale record: {str(e)}")
        flash('Error deleting sale record', 'error')
        return redirect(url_for('sales.records'))

@bp.route('/payments')
def payments():
    """Display all payment records."""
    try:
        payments = get_payment_records()
        return render_template('sales/payments.html', payments=payments)
    except Exception as e:
        logger.error(f"Error loading payment records: {str(e)}")
        flash('Error loading payment records', 'error')
        return redirect(url_for('main.index'))

@bp.route('/add_payment', methods=['POST'])
def add_payment():
    """Add a new payment record."""
    try:
        data = request.form.to_dict()
        if add_payment_record(data):
            flash('Payment record added successfully', 'success')
        else:
            flash('Failed to add payment record', 'error')
        return redirect(url_for('sales.payments'))
    except Exception as e:
        logger.error(f"Error adding payment record: {str(e)}")
        flash('Error adding payment record', 'error')
        return redirect(url_for('sales.payments'))

@bp.route('/payment_details/<payment_id>')
def payment_details(payment_id):
    """Get details of a specific payment."""
    try:
        payment = get_payment_details(payment_id)
        if payment:
            return jsonify(payment)
        return jsonify({'error': 'Payment not found'}), 404
    except Exception as e:
        logger.error(f"Error getting payment details: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/edit_payment/<payment_id>', methods=['GET', 'POST'])
def edit_payment(payment_id):
    """Edit a payment record."""
    try:
        if request.method == 'POST':
            data = request.form.to_dict()
            if update_payment_record(payment_id, data):
                flash('Payment record updated successfully', 'success')
            else:
                flash('Failed to update payment record', 'error')
            return redirect(url_for('sales.payments'))
        
        payment = get_payment_details(payment_id)
        if payment:
            return render_template('sales/edit_payment.html', payment=payment)
        flash('Payment not found', 'error')
        return redirect(url_for('sales.payments'))
    except Exception as e:
        logger.error(f"Error editing payment record: {str(e)}")
        flash('Error editing payment record', 'error')
        return redirect(url_for('sales.payments')) 