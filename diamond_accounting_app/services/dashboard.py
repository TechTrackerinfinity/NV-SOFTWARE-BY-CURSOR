from ..services.inventory import get_inventory_items, get_rough_inventory_items
from ..services.sales import get_sales_records, get_payment_records
from ..services.purchases import get_purchase_records
import pandas as pd
import logging
from datetime import datetime, timedelta

logger = logging.getLogger('diamond_app')

def get_dashboard_data():
    """Gather all data needed for the dashboard."""
    try:
        data = {
            'summary': get_summary_metrics(),
            'inventory': get_inventory_metrics(),
            'sales': get_sales_metrics(),
            'purchases': get_purchase_metrics(),
            'payments': get_payment_metrics(),
            'charts': get_chart_data()
        }
        return data
    except Exception as e:
        logger.error(f"Error gathering dashboard data: {str(e)}")
        return {}

def get_summary_metrics():
    """Get summary metrics for the dashboard."""
    try:
        inventory = get_inventory_items()
        rough_inventory = get_rough_inventory_items()
        sales = get_sales_records()
        purchases = get_purchase_records()
        payments = get_payment_records()
        
        # Calculate total values
        total_inventory_value = sum(item['price'] for item in inventory)
        total_rough_value = sum(item['purchase_price'] for item in rough_inventory)
        total_sales = sum(sale['amount'] for sale in sales)
        total_purchases = sum(purchase['amount'] for purchase in purchases)
        total_payments = sum(payment['amount'] for payment in payments)
        pending_payments = total_sales - total_payments
        
        return {
            'total_inventory_value': total_inventory_value,
            'total_rough_value': total_rough_value,
            'total_sales': total_sales,
            'total_purchases': total_purchases,
            'total_payments': total_payments,
            'pending_payments': pending_payments,
            'profit': total_sales - total_purchases
        }
    except Exception as e:
        logger.error(f"Error calculating summary metrics: {str(e)}")
        return {}

def get_inventory_metrics():
    """Get inventory-related metrics."""
    try:
        inventory = get_inventory_items()
        rough_inventory = get_rough_inventory_items()
        
        return {
            'total_items': len(inventory),
            'total_rough_items': len(rough_inventory),
            'total_carats': sum(item.get('carats', 0) for item in inventory),
            'total_rough_carats': sum(item.get('weight', 0) for item in rough_inventory),
            'avg_price_per_carat': calculate_avg_price_per_carat(inventory)
        }
    except Exception as e:
        logger.error(f"Error calculating inventory metrics: {str(e)}")
        return {}

def get_sales_metrics():
    """Get sales-related metrics."""
    try:
        sales = get_sales_records()
        
        # Get recent sales (last 30 days)
        recent_sales = [
            sale for sale in sales
            if (datetime.now() - datetime.strptime(sale['date'], '%Y-%m-%d')).days <= 30
        ]
        
        return {
            'total_sales_count': len(sales),
            'recent_sales_count': len(recent_sales),
            'avg_sale_value': sum(sale['amount'] for sale in sales) / len(sales) if sales else 0,
            'recent_sales_value': sum(sale['amount'] for sale in recent_sales)
        }
    except Exception as e:
        logger.error(f"Error calculating sales metrics: {str(e)}")
        return {}

def get_purchase_metrics():
    """Get purchase-related metrics."""
    try:
        purchases = get_purchase_records()
        
        # Get recent purchases (last 30 days)
        recent_purchases = [
            purchase for purchase in purchases
            if (datetime.now() - datetime.strptime(purchase['date'], '%Y-%m-%d')).days <= 30
        ]
        
        return {
            'total_purchases_count': len(purchases),
            'recent_purchases_count': len(recent_purchases),
            'avg_purchase_value': sum(purchase['amount'] for purchase in purchases) / len(purchases) if purchases else 0,
            'recent_purchases_value': sum(purchase['amount'] for purchase in recent_purchases)
        }
    except Exception as e:
        logger.error(f"Error calculating purchase metrics: {str(e)}")
        return {}

def get_payment_metrics():
    """Get payment-related metrics."""
    try:
        payments = get_payment_records()
        sales = get_sales_records()
        
        total_sales_amount = sum(sale['amount'] for sale in sales)
        total_payments_amount = sum(payment['amount'] for payment in payments)
        
        return {
            'total_payments': total_payments_amount,
            'pending_payments': total_sales_amount - total_payments_amount,
            'payment_ratio': (total_payments_amount / total_sales_amount * 100) if total_sales_amount > 0 else 0
        }
    except Exception as e:
        logger.error(f"Error calculating payment metrics: {str(e)}")
        return {}

def get_chart_data():
    """Get data for dashboard charts."""
    try:
        sales = get_sales_records()
        purchases = get_purchase_records()
        payments = get_payment_records()
        
        # Convert to pandas DataFrames for easier analysis
        sales_df = pd.DataFrame(sales)
        purchases_df = pd.DataFrame(purchases)
        payments_df = pd.DataFrame(payments)
        
        # Add date columns
        sales_df['date'] = pd.to_datetime(sales_df['date'])
        purchases_df['date'] = pd.to_datetime(purchases_df['date'])
        payments_df['date'] = pd.to_datetime(payments_df['date'])
        
        return {
            'monthly_sales': get_monthly_trend(sales_df, 'amount'),
            'monthly_purchases': get_monthly_trend(purchases_df, 'amount'),
            'monthly_payments': get_monthly_trend(payments_df, 'amount'),
            'payment_status': get_payment_status_distribution(sales_df, payments_df)
        }
    except Exception as e:
        logger.error(f"Error generating chart data: {str(e)}")
        return {}

def get_monthly_trend(df, value_column):
    """Calculate monthly trend for a DataFrame."""
    try:
        if df.empty:
            return []
        
        monthly = df.groupby(df['date'].dt.strftime('%Y-%m'))[value_column].sum()
        return [
            {'month': month, 'value': float(value)}
            for month, value in monthly.items()
        ]
    except Exception as e:
        logger.error(f"Error calculating monthly trend: {str(e)}")
        return []

def get_payment_status_distribution(sales_df, payments_df):
    """Calculate payment status distribution."""
    try:
        if sales_df.empty:
            return {'paid': 0, 'pending': 0}
        
        total_sales = sales_df['amount'].sum()
        total_payments = payments_df['amount'].sum() if not payments_df.empty else 0
        
        return {
            'paid': float(total_payments),
            'pending': float(total_sales - total_payments)
        }
    except Exception as e:
        logger.error(f"Error calculating payment distribution: {str(e)}")
        return {'paid': 0, 'pending': 0}

def calculate_avg_price_per_carat(inventory):
    """Calculate average price per carat for inventory items."""
    try:
        if not inventory:
            return 0
        
        total_price = sum(item['price'] for item in inventory)
        total_carats = sum(item.get('carats', 0) for item in inventory)
        
        return total_price / total_carats if total_carats > 0 else 0
    except Exception as e:
        logger.error(f"Error calculating average price per carat: {str(e)}")
        return 0 