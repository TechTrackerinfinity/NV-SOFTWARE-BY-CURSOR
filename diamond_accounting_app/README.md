# Shree Dangigev Diamonds (SDD) Accounting App

A simple web-based accounting application for Shree Dangigev Diamonds to track buying and selling transactions.

## Features

- User-friendly interface for recording transactions
- Separate sections for buying and selling diamonds
- Transaction details include date, item description, quantity, price, and total amount
- Data storage in Excel files for easy record-keeping
- Export and view past records
- Lightweight, secure, and efficient

## Setup Instructions

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Run the application:
   ```
   python app.py
   ```
6. Open your browser and navigate to `http://localhost:5000`

## Usage

1. Navigate to the "Buy" section to record diamond purchases
2. Navigate to the "Sell" section to record diamond sales
3. View transaction history in the "Records" section
4. Export data as needed for external reporting

## Data Storage

All transaction data is stored in Excel files in the `data` directory:
- `purchases.xlsx` - Records of all diamond purchases
- `sales.xlsx` - Records of all diamond sales

## Debugging Tools and Techniques

This application includes several debugging tools and techniques to help identify and resolve issues:

### Server-Side Debugging

1. **Logging System**
   - Comprehensive logging with different levels (DEBUG, INFO, WARNING, ERROR)
   - Log rotation to prevent log files from growing too large
   - Separate error log for critical issues
   - Detailed exception logging with tracebacks

2. **Error Handling**
   - Global error handlers for common HTTP errors (404, 500)
   - Try-except blocks in critical routes
   - User-friendly error pages
   - Detailed error reporting in logs

3. **Data Validation**
   - Data consistency checks
   - Data type validation
   - Automatic fixing of common data issues
   - Pre-restore backups for safety

### Client-Side Debugging

1. **JavaScript Debugging**
   - Custom DEBUG object with different log levels
   - Performance monitoring with timers
   - Detailed AJAX request logging
   - DOM element inspection utilities

2. **Form Validation**
   - Real-time validation feedback
   - Detailed error messages
   - Field-specific error reporting
   - Validation before submission

### Database Debugging

1. **Data Validation Tool**
   - Available at `/debug/validate_data` (debug mode only)
   - Checks for missing or corrupted files
   - Validates data consistency across files
   - Provides options to fix common issues

2. **Backup and Restore**
   - Regular automatic backups
   - Manual backup creation
   - Restore from backup with validation
   - Pre-restore backup for safety

### UI Debugging

1. **Responsive Design Testing**
   - Available at `/debug/responsive` (debug mode only)
   - Test pages at different screen sizes
   - Predefined device presets
   - Custom size testing

2. **Browser Compatibility**
   - Graceful degradation for older browsers
   - Feature detection instead of browser detection
   - Polyfills for missing features
   - Cross-browser testing utilities

## Usage

To run the application in debug mode:

```bash
python -m diamond_accounting_app.app
```

Debug mode enables:
- Detailed error pages
- Automatic reloading when code changes
- Access to debugging tools
- Verbose logging

## Important Notes

- Debug mode should be disabled in production
- Debug tools are only accessible when debug mode is enabled
- Logs are stored in the `logs` directory
- Backups are stored in the `data/backup` directory