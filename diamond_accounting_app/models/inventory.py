import pandas as pd
import os
from flask import current_app
import logging

logger = logging.getLogger('diamond_app')

__all__ = ['InventoryItem', 'get_inventory', 'add_inventory_item', 'update_inventory_item']

class InventoryItem:
    """Represents a diamond inventory item."""
    def __init__(self, item_id, carat, clarity, color, cut, price):
        self.item_id = item_id
        self.carat = float(carat)
        self.clarity = clarity
        self.color = color
        self.cut = cut
        self.price = float(price)
    
    @classmethod
    def from_dict(cls, data):
        """Create an InventoryItem from a dictionary."""
        return cls(
            item_id=data['item_id'],
            carat=data['carat'],
            clarity=data['clarity'],
            color=data['color'],
            cut=data['cut'],
            price=data['price']
        )
    
    def to_dict(self):
        """Convert the item to a dictionary."""
        return {
            'item_id': self.item_id,
            'carat': self.carat,
            'clarity': self.clarity,
            'color': self.color,
            'cut': self.cut,
            'price': self.price
        }

def get_inventory():
    """Get all inventory items."""
    try:
        inventory_file = os.path.join(current_app.config['DATA_DIR'], 'inventory.xlsx')
        df = pd.read_excel(inventory_file)
        return [InventoryItem.from_dict(row) for _, row in df.iterrows()]
    except Exception as e:
        logger.error(f"Error reading inventory: {str(e)}")
        return []

def add_inventory_item(item):
    """Add a new inventory item."""
    try:
        inventory_file = os.path.join(current_app.config['DATA_DIR'], 'inventory.xlsx')
        df = pd.read_excel(inventory_file) if os.path.exists(inventory_file) else pd.DataFrame()
        new_row = pd.DataFrame([item.to_dict()])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_excel(inventory_file, index=False)
        logger.info(f"Added inventory item: {item.item_id}")
        return True
    except Exception as e:
        logger.error(f"Error adding inventory item: {str(e)}")
        return False

def update_inventory_item(item):
    """Update an existing inventory item."""
    try:
        inventory_file = os.path.join(current_app.config['DATA_DIR'], 'inventory.xlsx')
        df = pd.read_excel(inventory_file)
        idx = df['item_id'] == item.item_id
        if not idx.any():
            logger.error(f"Inventory item not found: {item.item_id}")
            return False
        df.loc[idx] = pd.Series(item.to_dict())
        df.to_excel(inventory_file, index=False)
        logger.info(f"Updated inventory item: {item.item_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating inventory item: {str(e)}")
        return False 