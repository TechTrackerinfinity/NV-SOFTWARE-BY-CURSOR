from flask import Blueprint, render_template, request, jsonify
from ..services.reports import (
    get_dashboard_data,
    get_sales_report,
    get_purchases_report,
    get_inventory_report,
    get_payment_report,
    get_profit_loss_report
)
import logging

bp = Blueprint('reports', __name__)
logger = logging.getLogger('diamond_app')

@bp.route('/dashboard')
def dashboard():
    """Display the dashboard with key metrics and charts."""
    try:
        data = get_dashboard_data()
        return render_template('reports/dashboard.html', data=data)
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        flash('Error loading dashboard', 'error')
        return redirect(url_for('main.index'))

@bp.route('/reports')
def reports():
    """Display the main reports page."""
    try:
        return render_template('reports/reports.html')
    except Exception as e:
        logger.error(f"Error loading reports page: {str(e)}")
        flash('Error loading reports page', 'error')
        return redirect(url_for('main.index'))

@bp.route('/reports/sales', methods=['GET', 'POST'])
def sales_report():
    """Generate and display sales report."""
    try:
        filters = request.form.to_dict() if request.method == 'POST' else {}
        report_data = get_sales_report(filters)
        if request.method == 'POST':
            return jsonify(report_data)
        return render_template('reports/sales_report.html', data=report_data)
    except Exception as e:
        logger.error(f"Error generating sales report: {str(e)}")
        if request.method == 'POST':
            return jsonify({'error': 'Failed to generate report'}), 500
        flash('Error generating sales report', 'error')
        return redirect(url_for('reports.reports'))

@bp.route('/reports/purchases', methods=['GET', 'POST'])
def purchases_report():
    """Generate and display purchases report."""
    try:
        filters = request.form.to_dict() if request.method == 'POST' else {}
        report_data = get_purchases_report(filters)
        if request.method == 'POST':
            return jsonify(report_data)
        return render_template('reports/purchases_report.html', data=report_data)
    except Exception as e:
        logger.error(f"Error generating purchases report: {str(e)}")
        if request.method == 'POST':
            return jsonify({'error': 'Failed to generate report'}), 500
        flash('Error generating purchases report', 'error')
        return redirect(url_for('reports.reports'))

@bp.route('/reports/inventory', methods=['GET', 'POST'])
def inventory_report():
    """Generate and display inventory report."""
    try:
        filters = request.form.to_dict() if request.method == 'POST' else {}
        report_data = get_inventory_report(filters)
        if request.method == 'POST':
            return jsonify(report_data)
        return render_template('reports/inventory_report.html', data=report_data)
    except Exception as e:
        logger.error(f"Error generating inventory report: {str(e)}")
        if request.method == 'POST':
            return jsonify({'error': 'Failed to generate report'}), 500
        flash('Error generating inventory report', 'error')
        return redirect(url_for('reports.reports'))

@bp.route('/reports/payments', methods=['GET', 'POST'])
def payment_report():
    """Generate and display payment report."""
    try:
        filters = request.form.to_dict() if request.method == 'POST' else {}
        report_data = get_payment_report(filters)
        if request.method == 'POST':
            return jsonify(report_data)
        return render_template('reports/payment_report.html', data=report_data)
    except Exception as e:
        logger.error(f"Error generating payment report: {str(e)}")
        if request.method == 'POST':
            return jsonify({'error': 'Failed to generate report'}), 500
        flash('Error generating payment report', 'error')
        return redirect(url_for('reports.reports'))

@bp.route('/reports/profit-loss', methods=['GET', 'POST'])
def profit_loss_report():
    """Generate and display profit & loss report."""
    try:
        filters = request.form.to_dict() if request.method == 'POST' else {}
        report_data = get_profit_loss_report(filters)
        if request.method == 'POST':
            return jsonify(report_data)
        return render_template('reports/profit_loss_report.html', data=report_data)
    except Exception as e:
        logger.error(f"Error generating profit & loss report: {str(e)}")
        if request.method == 'POST':
            return jsonify({'error': 'Failed to generate report'}), 500
        flash('Error generating profit & loss report', 'error')
        return redirect(url_for('reports.reports')) 