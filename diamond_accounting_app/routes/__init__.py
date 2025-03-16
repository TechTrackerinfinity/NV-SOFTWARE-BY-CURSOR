from .inventory import bp as inventory_bp
from .sales import bp as sales_bp
from .purchases import bp as purchases_bp
from .reports import bp as reports_bp
from .main import bp as main_bp
from .backup import bp as backup_bp
from .debug import bp as debug_bp

__all__ = [
    'main_bp',
    'inventory_bp',
    'sales_bp',
    'purchases_bp',
    'reports_bp',
    'backup_bp',
    'debug_bp'
] 