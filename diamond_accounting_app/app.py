import os
import pandas as pd
import numpy as np
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
import shutil
import zipfile
import tempfile
from datetime import datetime, timedelta
import json
import re
import hashlib
import time
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import base64
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'diamond_business_secret_key'

# Ensure data directory exists
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# Define file paths
PURCHASES_FILE = os.path.join(DATA_DIR, 'purchases.xlsx')
SALES_FILE = os.path.join(DATA_DIR, 'sales.xlsx')
PAYMENTS_FILE = os.path.join(DATA_DIR, 'payments.xlsx')
INVENTORY_FILE = 'data/inventory.xlsx'

# Function to enhance Excel file formatting
def enhance_excel_formatting(file_path, sheet_name='Sheet1'):
    # Load the workbook
    try:
        from openpyxl import load_workbook, Workbook
        
        # Check if file exists first
        if not os.path.exists(file_path):
            # Create a new workbook if file doesn't exist
            wb = Workbook()
            sheet = wb.active
            sheet.title = sheet_name
            wb.save(file_path)
            print(f"Created new Excel file at {file_path}")
        
        # Load the workbook directly with openpyxl
        wb = load_workbook(file_path)
        
        # Get the active sheet
        if sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
        else:
            # If the specified sheet doesn't exist, use the active sheet
            sheet = wb.active
            # Only set title if it's not already set
            if sheet is not None:
                sheet.title = sheet_name
        
        # Ensure sheet is not None before proceeding
        if sheet is None:
            raise ValueError(f"Could not find or create sheet '{sheet_name}' in workbook")
        
        # Format headers
        if sheet.max_row > 0:  # Only proceed if there are rows in the sheet
            for col_num, column_title in enumerate(sheet[1], 1):
                if column_title is None or column_title.value is None:
                    continue
                
                cell = sheet.cell(row=1, column=col_num)
                cell.font = Font(name='Arial', size=12, bold=True, color='FFFFFF')
                cell.fill = PatternFill(start_color='4F81BD', end_color='4F81BD', fill_type='solid')
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                cell.border = Border(
                    left=Side(style='thin', color='000000'),
                    right=Side(style='thin', color='000000'),
                    top=Side(style='thin', color='000000'),
                    bottom=Side(style='thin', color='000000')
                )
                
                # Adjust column width based on content
                column_letter = get_column_letter(col_num)
                max_length = 0
                for cell in sheet[column_letter]:
                    try:
                        if cell.value and len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2) * 1.2
                sheet.column_dimensions[column_letter].width = min(adjusted_width, 30)
        
            # Format data cells
            for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row):
                for cell in row:
                    cell.border = Border(
                        left=Side(style='thin', color='000000'),
                        right=Side(style='thin', color='000000'),
                        top=Side(style='thin', color='000000'),
                        bottom=Side(style='thin', color='000000')
                    )
                    
                    # Align numeric values to the right
                    if isinstance(cell.value, (int, float)):
                        cell.alignment = Alignment(horizontal='right', vertical='center')
                        cell.number_format = '#,##0.00'
                    else:
                        cell.alignment = Alignment(vertical='center')
        
            # Add conditional formatting for payment status
            status_column = None
            for col_num, column_title in enumerate(sheet[1], 1):
                if column_title.value == 'Payment Status':
                    status_column = get_column_letter(col_num)
                    break
            
            if status_column:
                # Pending - Light Red
                pending_rule = CellIsRule(operator='equal', formula=['"Pending"'], 
                                        stopIfTrue=True, fill=PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid'))
                sheet.conditional_formatting.add(f'{status_column}2:{status_column}{sheet.max_row}', pending_rule)
                
                # Completed - Light Green
                completed_rule = CellIsRule(operator='equal', formula=['"Completed"'], 
                                        stopIfTrue=True, fill=PatternFill(start_color='CCFFCC', end_color='CCFFCC', fill_type='solid'))
                sheet.conditional_formatting.add(f'{status_column}2:{status_column}{sheet.max_row}', completed_rule)
                
                # Partial - Light Yellow
                partial_rule = CellIsRule(operator='equal', formula=['"Partial"'], 
                                        stopIfTrue=True, fill=PatternFill(start_color='FFFFCC', end_color='FFFFCC', fill_type='solid'))
                sheet.conditional_formatting.add(f'{status_column}2:{status_column}{sheet.max_row}', partial_rule)
            
            # Format amount columns
            for col_num, column_title in enumerate(sheet[1], 1):
                if column_title.value and 'Amount' in str(column_title.value):
                    column_letter = get_column_letter(col_num)
                    for row in range(2, sheet.max_row + 1):
                        cell = sheet[f'{column_letter}{row}']
                        cell.number_format = '#,##0.00'
                        
                        # Add currency symbol based on column name
                        if 'USD' in str(column_title.value):
                            cell.number_format = '"$"#,##0.00'
                        elif 'INR' in str(column_title.value):
                            cell.number_format = '"₹"#,##0.00'
            
            # Format date columns
            for col_num, column_title in enumerate(sheet[1], 1):
                if column_title.value and 'Date' in str(column_title.value):
                    column_letter = get_column_letter(col_num)
                    for row in range(2, sheet.max_row + 1):
                        cell = sheet[f'{column_letter}{row}']
                        if cell.value:
                            cell.number_format = 'yyyy-mm-dd'
            
            # Add alternating row colors for better readability
            for row in range(2, sheet.max_row + 1):
                if row % 2 == 0:  # Even rows
                    for col in range(1, sheet.max_column + 1):
                        cell = sheet.cell(row=row, column=col)
                        if not cell.fill.start_color.index == 'FFCCCC' and not cell.fill.start_color.index == 'CCFFCC' and not cell.fill.start_color.index == 'FFFFCC':
                            cell.fill = PatternFill(start_color='F5F5F5', end_color='F5F5F5', fill_type='solid')
            
            # Freeze the header row
            sheet.freeze_panes = 'A2'
            
            # Add data validation for Payment Status column if it exists
            if status_column:
                from openpyxl.worksheet.datavalidation import DataValidation
                dv = DataValidation(type="list", formula1='"Pending,Completed,Partial"', allow_blank=True)
                sheet.add_data_validation(dv)
                dv.add(f'{status_column}2:{status_column}{sheet.max_row}')
        
        # Save the workbook
        wb.save(file_path)
        print(f"Successfully enhanced Excel formatting for {file_path}")
        
        # Create summary sheet if there's enough data
        if sheet.max_row > 1:
            try:
                create_summary_sheet(file_path)
                create_dashboard(file_path)
            except Exception as e:
                print(f"Error creating summary or dashboard: {str(e)}")
        
        return file_path
    except Exception as e:
        print(f"Error in enhance_excel_formatting: {str(e)}")
        # Return the original file path even if formatting failed
        return file_path

# Function to create a summary sheet with charts and key metrics
def create_summary_sheet(file_path):
    try:
        from openpyxl import load_workbook
        from openpyxl.chart import PieChart, BarChart, Reference
        from openpyxl.chart.series import DataPoint
        
        # Load the workbook
        wb = load_workbook(file_path)
        
        # Ensure there's at least one sheet in the workbook
        if len(wb.sheetnames) == 0:
            print(f"Error: No sheets found in workbook {file_path}")
            return
            
        data_sheet = wb.active
        
        # Check if summary sheet already exists, if not create it
        if 'Summary' in wb.sheetnames:
            wb.remove(wb['Summary'])
        
        summary_sheet = wb.create_sheet(title='Summary')
        
        # Set column widths
        for col in range(1, 10):
            summary_sheet.column_dimensions[get_column_letter(col)].width = 15
        
        # Add title
        summary_sheet['A1'] = 'Diamond Transaction Summary'
        summary_sheet['A1'].font = Font(name='Arial', size=16, bold=True)
        summary_sheet.merge_cells('A1:I1')
        summary_sheet['A1'].alignment = Alignment(horizontal='center')
        
        # Add section headers
        summary_sheet['A3'] = 'Key Metrics'
        summary_sheet['A3'].font = Font(name='Arial', size=14, bold=True)
        summary_sheet['A3'].fill = PatternFill(start_color='4F81BD', end_color='4F81BD', fill_type='solid')
        summary_sheet['A3'].font = Font(color='FFFFFF', bold=True)
        summary_sheet.merge_cells('A3:I3')
        summary_sheet['A3'].alignment = Alignment(horizontal='center')
        
        # Calculate key metrics
        total_records = max(0, data_sheet.max_row - 1)  # Ensure it's not negative
        
        # Find column indices
        carat_col = None
        amount_usd_col = None
        amount_inr_col = None
        status_col = None
        date_col = None
        
        # Check if data_sheet has any rows before trying to access them
        if data_sheet.max_row > 0:
            for col_num, cell in enumerate(data_sheet[1], 1):
                if cell.value == 'Carat':
                    carat_col = col_num
                elif cell.value == 'Total Amount USD':
                    amount_usd_col = col_num
                elif cell.value == 'Total Amount INR':
                    amount_inr_col = col_num
                elif cell.value == 'Payment Status':
                    status_col = col_num
                elif cell.value == 'Date':
                    date_col = col_num
        
        # Calculate totals
        total_carat = 0
        total_amount_usd = 0
        total_amount_inr = 0
        pending_count = 0
        completed_count = 0
        partial_count = 0
        
        for row in range(2, data_sheet.max_row + 1):
            if carat_col:
                carat_value = data_sheet.cell(row=row, column=carat_col).value
                if carat_value and isinstance(carat_value, (int, float)):
                    total_carat += carat_value
            
            if amount_usd_col:
                amount_value = data_sheet.cell(row=row, column=amount_usd_col).value
                if amount_value and isinstance(amount_value, (int, float)):
                    total_amount_usd += amount_value
            
            if amount_inr_col:
                amount_value = data_sheet.cell(row=row, column=amount_inr_col).value
                if amount_value and isinstance(amount_value, (int, float)):
                    total_amount_inr += amount_value
            
            if status_col:
                status_value = data_sheet.cell(row=row, column=status_col).value
                if status_value == 'Pending':
                    pending_count += 1
                elif status_value == 'Completed':
                    completed_count += 1
                elif status_value == 'Partial':
                    partial_count += 1
        
        # Add metrics to summary sheet
        summary_sheet['A5'] = 'Total Records:'
        summary_sheet['B5'] = total_records
        summary_sheet['A5'].font = Font(bold=True)
        
        summary_sheet['A6'] = 'Total Carat:'
        summary_sheet['B6'] = total_carat
        summary_sheet['B6'].number_format = '#,##0.00'
        summary_sheet['A6'].font = Font(bold=True)
        
        summary_sheet['A7'] = 'Total Amount (USD):'
        summary_sheet['B7'] = total_amount_usd
        summary_sheet['B7'].number_format = '"$"#,##0.00'
        summary_sheet['A7'].font = Font(bold=True)
        
        summary_sheet['A8'] = 'Total Amount (INR):'
        summary_sheet['B8'] = total_amount_inr
        summary_sheet['B8'].number_format = '"₹"#,##0.00'
        summary_sheet['A8'].font = Font(bold=True)
        
        summary_sheet['A9'] = 'Pending Payments:'
        summary_sheet['B9'] = pending_count
        summary_sheet['A9'].font = Font(bold=True)
        
        summary_sheet['A10'] = 'Completed Payments:'
        summary_sheet['B10'] = completed_count
        summary_sheet['A10'].font = Font(bold=True)
        
        summary_sheet['A11'] = 'Partial Payments:'
        summary_sheet['B11'] = partial_count
        summary_sheet['A11'].font = Font(bold=True)
        
        # Add borders to metrics
        for row in range(5, 12):
            for col in range(1, 3):
                cell = summary_sheet.cell(row=row, column=col)
                cell.border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
        
        # Add payment status chart
        if status_col and (pending_count > 0 or completed_count > 0 or partial_count > 0):
            summary_sheet['A13'] = 'Payment Status Distribution'
            summary_sheet['A13'].font = Font(name='Arial', size=14, bold=True)
            summary_sheet['A13'].fill = PatternFill(start_color='4F81BD', end_color='4F81BD', fill_type='solid')
            summary_sheet['A13'].font = Font(color='FFFFFF', bold=True)
            summary_sheet.merge_cells('A13:I13')
            summary_sheet['A13'].alignment = Alignment(horizontal='center')
            
            # Create data for pie chart
            summary_sheet['A15'] = 'Status'
            summary_sheet['B15'] = 'Count'
            summary_sheet['A15'].font = Font(bold=True)
            summary_sheet['B15'].font = Font(bold=True)
            
            summary_sheet['A16'] = 'Pending'
            summary_sheet['B16'] = pending_count
            
            summary_sheet['A17'] = 'Completed'
            summary_sheet['B17'] = completed_count
            
            summary_sheet['A18'] = 'Partial'
            summary_sheet['B18'] = partial_count
            
            # Create pie chart
            pie = PieChart()
            labels = Reference(summary_sheet, min_col=1, min_row=16, max_row=18)
            data = Reference(summary_sheet, min_col=2, min_row=15, max_row=18)
            pie.add_data(data, titles_from_data=True)
            pie.set_categories(labels)
            pie.title = "Payment Status Distribution"
            
            # Add custom colors to pie chart slices
            slice1 = DataPoint(idx=0, fill=PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid'))
            slice2 = DataPoint(idx=1, fill=PatternFill(start_color='CCFFCC', end_color='CCFFCC', fill_type='solid'))
            slice3 = DataPoint(idx=2, fill=PatternFill(start_color='FFFFCC', end_color='FFFFCC', fill_type='solid'))
            pie.series[0].data_points = [slice1, slice2, slice3]
            
            pie.height = 10
            pie.width = 10
            summary_sheet.add_chart(pie, "D15")
        
        # Add monthly trend if date column exists
        if date_col and total_records > 0:
            summary_sheet['A25'] = 'Monthly Transaction Trend'
            summary_sheet['A25'].font = Font(name='Arial', size=14, bold=True)
            summary_sheet['A25'].fill = PatternFill(start_color='4F81BD', end_color='4F81BD', fill_type='solid')
            summary_sheet['A25'].font = Font(color='FFFFFF', bold=True)
            summary_sheet.merge_cells('A25:I25')
            summary_sheet['A25'].alignment = Alignment(horizontal='center')
            
            # Collect monthly data
            monthly_data = {}
            
            for row in range(2, data_sheet.max_row + 1):
                date_value = data_sheet.cell(row=row, column=date_col).value
                if date_value:
                    try:
                        if isinstance(date_value, str):
                            date_value = datetime.strptime(date_value, '%Y-%m-%d')
                        
                        month_key = f"{date_value.year}-{date_value.month:02d}"
                        
                        if month_key not in monthly_data:
                            monthly_data[month_key] = {
                                'count': 0,
                                'amount_usd': 0,
                                'amount_inr': 0
                            }
                        
                        monthly_data[month_key]['count'] += 1
                        
                        if amount_usd_col:
                            amount_value = data_sheet.cell(row=row, column=amount_usd_col).value
                            if amount_value and isinstance(amount_value, (int, float)):
                                monthly_data[month_key]['amount_usd'] += amount_value
                        
                        if amount_inr_col:
                            amount_value = data_sheet.cell(row=row, column=amount_inr_col).value
                            if amount_value and isinstance(amount_value, (int, float)):
                                monthly_data[month_key]['amount_inr'] += amount_value
                    except Exception as e:
                        print(f"Error processing date in row {row}: {str(e)}")
                        continue
            
            # Sort months chronologically
            sorted_months = sorted(monthly_data.keys())
            
            # Add data for bar chart
            summary_sheet['A27'] = 'Month'
            summary_sheet['B27'] = 'Count'
            summary_sheet['C27'] = 'Amount (USD)'
            summary_sheet['D27'] = 'Amount (INR)'
            
            summary_sheet['A27'].font = Font(bold=True)
            summary_sheet['B27'].font = Font(bold=True)
            summary_sheet['C27'].font = Font(bold=True)
            summary_sheet['D27'].font = Font(bold=True)
            
            for i, month in enumerate(sorted_months, 28):
                summary_sheet[f'A{i}'] = month
                summary_sheet[f'B{i}'] = monthly_data[month]['count']
                summary_sheet[f'C{i}'] = monthly_data[month]['amount_usd']
                summary_sheet[f'D{i}'] = monthly_data[month]['amount_inr']
                
                summary_sheet[f'C{i}'].number_format = '"$"#,##0.00'
                summary_sheet[f'D{i}'].number_format = '"₹"#,##0.00'
            
            # Create bar chart for transaction count
            if len(sorted_months) > 0:
                chart = BarChart()
                chart.type = "col"
                chart.style = 10
                chart.title = "Monthly Transaction Count"
                chart.y_axis.title = "Number of Transactions"
                chart.x_axis.title = "Month"
                
                data = Reference(summary_sheet, min_col=2, min_row=27, max_row=27+len(sorted_months))
                cats = Reference(summary_sheet, min_col=1, min_row=28, max_row=27+len(sorted_months))
                chart.add_data(data, titles_from_data=True)
                chart.set_categories(cats)
                chart.shape = 4
                chart.height = 10
                chart.width = 15
                
                summary_sheet.add_chart(chart, "F27")
        
        # Apply styling to the entire summary sheet
        for row in summary_sheet.iter_rows():
            for cell in row:
                if not cell.font.bold:
                    cell.font = Font(name='Arial')
        
        # Save the workbook
        wb.save(file_path)
    except Exception as e:
        print(f"Error in create_summary_sheet: {str(e)}")
        # Don't re-raise the exception, just log it and continue

# Function to create a dashboard with visual elements
def create_dashboard(file_path):
    try:
        from openpyxl import load_workbook
        from openpyxl.chart import PieChart, BarChart, LineChart, Reference
        from openpyxl.chart.series import DataPoint
        from openpyxl.drawing.image import Image
        
        # Load the workbook
        wb = load_workbook(file_path)
        
        # Ensure there's at least one sheet in the workbook
        if len(wb.sheetnames) == 0:
            print(f"Error: No sheets found in workbook {file_path}")
            return
            
        data_sheet = wb.active
        
        # Check if dashboard sheet already exists, if not create it
        if 'Dashboard' in wb.sheetnames:
            wb.remove(wb['Dashboard'])
        
        dashboard = wb.create_sheet(title='Dashboard', index=0)  # Make it the first sheet
        
        # Set column widths
        for col in range(1, 15):
            dashboard.column_dimensions[get_column_letter(col)].width = 15
        
        # Add title
        dashboard['A1'] = 'DIAMOND BUSINESS DASHBOARD'
        dashboard['A1'].font = Font(name='Arial', size=20, bold=True, color='4F81BD')
        dashboard.merge_cells('A1:N1')
        dashboard['A1'].alignment = Alignment(horizontal='center')
        
        # Add subtitle with current date
        current_date = datetime.now().strftime('%Y-%m-%d')
        dashboard['A2'] = f'Generated on: {current_date}'
        dashboard['A2'].font = Font(name='Arial', size=10, italic=True)
        dashboard.merge_cells('A2:N2')
        dashboard['A2'].alignment = Alignment(horizontal='center')
        
        # Find column indices
        carat_col = None
        amount_usd_col = None
        amount_inr_col = None
        status_col = None
        date_col = None
        
        # Check if data_sheet has any rows before trying to access them
        if data_sheet.max_row > 0:
            for col_num, cell in enumerate(data_sheet[1], 1):
                if cell.value == 'Carat':
                    carat_col = col_num
                elif cell.value == 'Total Amount USD':
                    amount_usd_col = col_num
                elif cell.value == 'Total Amount INR':
                    amount_inr_col = col_num
                elif cell.value == 'Payment Status':
                    status_col = col_num
                elif cell.value == 'Date':
                    date_col = col_num
        
        # Calculate key metrics
        total_records = max(0, data_sheet.max_row - 1)  # Ensure it's not negative
        total_carat = 0
        total_amount_usd = 0
        total_amount_inr = 0
        pending_count = 0
        completed_count = 0
        partial_count = 0
        
        # Data for monthly trends
        monthly_data = {}
        
        for row in range(2, data_sheet.max_row + 1):
            if carat_col:
                carat_value = data_sheet.cell(row=row, column=carat_col).value
                if carat_value and isinstance(carat_value, (int, float)):
                    total_carat += carat_value
            
            if amount_usd_col:
                amount_value = data_sheet.cell(row=row, column=amount_usd_col).value
                if amount_value and isinstance(amount_value, (int, float)):
                    total_amount_usd += amount_value
            
            if amount_inr_col:
                amount_value = data_sheet.cell(row=row, column=amount_inr_col).value
                if amount_value and isinstance(amount_value, (int, float)):
                    total_amount_inr += amount_value
            
            if status_col:
                status_value = data_sheet.cell(row=row, column=status_col).value
                if status_value == 'Pending':
                    pending_count += 1
                elif status_value == 'Completed':
                    completed_count += 1
                elif status_value == 'Partial':
                    partial_count += 1
            
            # Collect monthly data
            if date_col:
                date_value = data_sheet.cell(row=row, column=date_col).value
                if date_value:
                    try:
                        if isinstance(date_value, str):
                            date_value = datetime.strptime(date_value, '%Y-%m-%d')
                        
                        month_key = f"{date_value.year}-{date_value.month:02d}"
                        month_name = f"{calendar.month_name[date_value.month]} {date_value.year}"
                        
                        if month_key not in monthly_data:
                            monthly_data[month_key] = {
                                'name': month_name,
                                'count': 0,
                                'amount_usd': 0,
                                'amount_inr': 0,
                                'carat': 0
                            }
                        
                        monthly_data[month_key]['count'] += 1
                        
                        if amount_usd_col:
                            amount_value = data_sheet.cell(row=row, column=amount_usd_col).value
                            if amount_value and isinstance(amount_value, (int, float)):
                                monthly_data[month_key]['amount_usd'] += amount_value
                        
                        if amount_inr_col:
                            amount_value = data_sheet.cell(row=row, column=amount_inr_col).value
                            if amount_value and isinstance(amount_value, (int, float)):
                                monthly_data[month_key]['amount_inr'] += amount_value
                        
                        if carat_col:
                            carat_value = data_sheet.cell(row=row, column=carat_col).value
                            if carat_value and isinstance(carat_value, (int, float)):
                                monthly_data[month_key]['carat'] += carat_value
                    except Exception as e:
                        print(f"Error processing date in row {row}: {str(e)}")
                        continue
        
        # Sort months chronologically
        sorted_months = sorted(monthly_data.keys())
        
        # Create KPI cards
        dashboard['A4'] = 'KEY PERFORMANCE INDICATORS'
        dashboard['A4'].font = Font(name='Arial', size=14, bold=True, color='FFFFFF')
        dashboard['A4'].fill = PatternFill(start_color='4F81BD', end_color='4F81BD', fill_type='solid')
        dashboard.merge_cells('A4:N4')
        dashboard['A4'].alignment = Alignment(horizontal='center')
        
        # KPI Card 1: Total Records
        dashboard['B6'] = 'Total Records'
        dashboard['B6'].font = Font(name='Arial', size=12, bold=True)
        dashboard['B6'].alignment = Alignment(horizontal='center')
        dashboard.merge_cells('B6:D6')
        
        dashboard['B7'] = total_records
        dashboard['B7'].font = Font(name='Arial', size=24, bold=True, color='4F81BD')
        dashboard['B7'].alignment = Alignment(horizontal='center')
        dashboard.merge_cells('B7:D7')
        
        # Add border to KPI card
        for row in range(6, 8):
            for col in range(2, 5):
                cell = dashboard.cell(row=row, column=col)
                cell.border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
        
        # KPI Card 2: Total Carat
        dashboard['F6'] = 'Total Carat'
        dashboard['F6'].font = Font(name='Arial', size=12, bold=True)
        dashboard['F6'].alignment = Alignment(horizontal='center')
        dashboard.merge_cells('F6:H6')
        
        dashboard['F7'] = total_carat
        dashboard['F7'].font = Font(name='Arial', size=24, bold=True, color='4F81BD')
        dashboard['F7'].alignment = Alignment(horizontal='center')
        dashboard['F7'].number_format = '#,##0.00'
        dashboard.merge_cells('F7:H7')
        
        # Add border to KPI card
        for row in range(6, 8):
            for col in range(6, 9):
                cell = dashboard.cell(row=row, column=col)
                cell.border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
        
        # KPI Card 3: Total Amount USD
        dashboard['J6'] = 'Total Amount (USD)'
        dashboard['J6'].font = Font(name='Arial', size=12, bold=True)
        dashboard['J6'].alignment = Alignment(horizontal='center')
        dashboard.merge_cells('J6:L6')
        
        dashboard['J7'] = total_amount_usd
        dashboard['J7'].font = Font(name='Arial', size=24, bold=True, color='4F81BD')
        dashboard['J7'].alignment = Alignment(horizontal='center')
        dashboard['J7'].number_format = '"$"#,##0.00'
        dashboard.merge_cells('J7:L7')
        
        # Add border to KPI card
        for row in range(6, 8):
            for col in range(10, 13):
                cell = dashboard.cell(row=row, column=col)
                cell.border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
        
        # KPI Card 4: Total Amount INR
        dashboard['B9'] = 'Total Amount (INR)'
        dashboard['B9'].font = Font(name='Arial', size=12, bold=True)
        dashboard['B9'].alignment = Alignment(horizontal='center')
        dashboard.merge_cells('B9:D9')
        
        dashboard['B10'] = total_amount_inr
        dashboard['B10'].font = Font(name='Arial', size=24, bold=True, color='4F81BD')
        dashboard['B10'].alignment = Alignment(horizontal='center')
        dashboard['B10'].number_format = '"₹"#,##0.00'
        dashboard.merge_cells('B10:D10')
        
        # Add border to KPI card
        for row in range(9, 11):
            for col in range(2, 5):
                cell = dashboard.cell(row=row, column=col)
                cell.border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
        
        # KPI Card 5: Pending Payments
        dashboard['F9'] = 'Pending Payments'
        dashboard['F9'].font = Font(name='Arial', size=12, bold=True)
        dashboard['F9'].alignment = Alignment(horizontal='center')
        dashboard.merge_cells('F9:H9')
        
        dashboard['F10'] = pending_count
        dashboard['F10'].font = Font(name='Arial', size=24, bold=True, color='FF0000')
        dashboard['F10'].alignment = Alignment(horizontal='center')
        dashboard.merge_cells('F10:H10')
        
        # Add border to KPI card
        for row in range(9, 11):
            for col in range(6, 9):
                cell = dashboard.cell(row=row, column=col)
                cell.border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
        
        # KPI Card 6: Completed Payments
        dashboard['J9'] = 'Completed Payments'
        dashboard['J9'].font = Font(name='Arial', size=12, bold=True)
        dashboard['J9'].alignment = Alignment(horizontal='center')
        dashboard.merge_cells('J9:L9')
        
        dashboard['J10'] = completed_count
        dashboard['J10'].font = Font(name='Arial', size=24, bold=True, color='008000')
        dashboard['J10'].alignment = Alignment(horizontal='center')
        dashboard.merge_cells('J10:L10')
        
        # Add border to KPI card
        for row in range(9, 11):
            for col in range(10, 13):
                cell = dashboard.cell(row=row, column=col)
                cell.border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
        
        # Add Payment Status Chart
        if status_col and (pending_count > 0 or completed_count > 0 or partial_count > 0):
            dashboard['A12'] = 'PAYMENT STATUS DISTRIBUTION'
            dashboard['A12'].font = Font(name='Arial', size=14, bold=True, color='FFFFFF')
            dashboard['A12'].fill = PatternFill(start_color='4F81BD', end_color='4F81BD', fill_type='solid')
            dashboard.merge_cells('A12:N12')
            dashboard['A12'].alignment = Alignment(horizontal='center')
            
            # Create data for pie chart
            dashboard['B14'] = 'Status'
            dashboard['C14'] = 'Count'
            dashboard['B14'].font = Font(bold=True)
            dashboard['C14'].font = Font(bold=True)
            
            dashboard['B15'] = 'Pending'
            dashboard['C15'] = pending_count
            dashboard['B15'].fill = PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid')
            
            dashboard['B16'] = 'Completed'
            dashboard['C16'] = completed_count
            dashboard['B16'].fill = PatternFill(start_color='CCFFCC', end_color='CCFFCC', fill_type='solid')
            
            dashboard['B17'] = 'Partial'
            dashboard['C17'] = partial_count
            dashboard['B17'].fill = PatternFill(start_color='FFFFCC', end_color='FFFFCC', fill_type='solid')
            
            # Create pie chart
            pie = PieChart()
            labels = Reference(dashboard, min_col=2, min_row=15, max_row=17)
            data = Reference(dashboard, min_col=3, min_row=14, max_row=17)
            pie.add_data(data, titles_from_data=True)
            pie.set_categories(labels)
            pie.title = "Payment Status Distribution"
            
            # Add custom colors to pie chart slices
            slice1 = DataPoint(idx=0, fill=PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid'))
            slice2 = DataPoint(idx=1, fill=PatternFill(start_color='CCFFCC', end_color='CCFFCC', fill_type='solid'))
            slice3 = DataPoint(idx=2, fill=PatternFill(start_color='FFFFCC', end_color='FFFFCC', fill_type='solid'))
            pie.series[0].data_points = [slice1, slice2, slice3]
            
            pie.height = 10
            pie.width = 10
            dashboard.add_chart(pie, "E14")
        
        # Add Monthly Trend Charts
        if date_col and len(sorted_months) > 0:
            dashboard['A22'] = 'MONTHLY TRENDS'
            dashboard['A22'].font = Font(name='Arial', size=14, bold=True, color='FFFFFF')
            dashboard['A22'].fill = PatternFill(start_color='4F81BD', end_color='4F81BD', fill_type='solid')
            dashboard.merge_cells('A22:N22')
            dashboard['A22'].alignment = Alignment(horizontal='center')
            
            # Create data for charts
            dashboard['B24'] = 'Month'
            dashboard['C24'] = 'Transactions'
            dashboard['D24'] = 'Amount (USD)'
            dashboard['E24'] = 'Amount (INR)'
            dashboard['F24'] = 'Carat'
            
            dashboard['B24'].font = Font(bold=True)
            dashboard['C24'].font = Font(bold=True)
            dashboard['D24'].font = Font(bold=True)
            dashboard['E24'].font = Font(bold=True)
            dashboard['F24'].font = Font(bold=True)
            
            for i, month_key in enumerate(sorted_months, 25):
                month_data = monthly_data[month_key]
                dashboard[f'B{i}'] = month_data['name']
                dashboard[f'C{i}'] = month_data['count']
                dashboard[f'D{i}'] = month_data['amount_usd']
                dashboard[f'E{i}'] = month_data['amount_inr']
                dashboard[f'F{i}'] = month_data['carat']
                
                dashboard[f'D{i}'].number_format = '"$"#,##0.00'
                dashboard[f'E{i}'].number_format = '"₹"#,##0.00'
                dashboard[f'F{i}'].number_format = '#,##0.00'
            
            # Create line chart for monthly transactions
            line = LineChart()
            line.title = "Monthly Transaction Count"
            line.style = 12
            line.y_axis.title = "Number of Transactions"
            line.x_axis.title = "Month"
            
            data = Reference(dashboard, min_col=3, min_row=24, max_row=24+len(sorted_months))
            cats = Reference(dashboard, min_col=2, min_row=25, max_row=24+len(sorted_months))
            line.add_data(data, titles_from_data=True)
            line.set_categories(cats)
            
            line.height = 10
            line.width = 15
            dashboard.add_chart(line, "H24")
            
            # Create line chart for monthly carat
            line2 = LineChart()
            line2.title = "Monthly Carat Volume"
            line2.style = 13
            line2.y_axis.title = "Total Carat"
            line2.x_axis.title = "Month"
            
            data = Reference(dashboard, min_col=6, min_row=24, max_row=24+len(sorted_months))
            cats = Reference(dashboard, min_col=2, min_row=25, max_row=24+len(sorted_months))
            line2.add_data(data, titles_from_data=True)
            line2.set_categories(cats)
            
            line2.height = 10
            line2.width = 15
            dashboard.add_chart(line2, "H38")
        
        # Add footer
        footer_row = dashboard.max_row + 5
        dashboard[f'A{footer_row}'] = 'Generated by Diamond Accounting App'
        dashboard[f'A{footer_row}'].font = Font(name='Arial', size=10, italic=True)
        dashboard.merge_cells(f'A{footer_row}:N{footer_row}')
        dashboard[f'A{footer_row}'].alignment = Alignment(horizontal='center')
        
        # Save the workbook
        wb.save(file_path)
    except Exception as e:
        print(f"Error in create_dashboard: {str(e)}")
        # Don't re-raise the exception, just log it and continue

# Initialize Excel files if they don't exist
def initialize_excel_files():
    """Initialize Excel files if they don't exist."""
    os.makedirs('data', exist_ok=True)
    
    # Initialize purchases file
    if not os.path.exists(PURCHASES_FILE):
        df = pd.DataFrame(columns=['Date', 'Party', 'Diamond Type', 'Carats', 'Rate per Carat', 
                                  'Total Amount USD', 'Exchange Rate', 'Total Amount INR', 'Payment Status', 'Notes'])
        df.to_excel(PURCHASES_FILE, index=False)
        enhance_excel_formatting(PURCHASES_FILE)
    
    # Initialize sales file
    if not os.path.exists(SALES_FILE):
        df = pd.DataFrame(columns=['Date', 'Party', 'Diamond Type', 'Carats', 'Rate per Carat', 
                                  'Total Amount USD', 'Exchange Rate', 'Total Amount INR', 'Payment Status', 'Notes'])
        df.to_excel(SALES_FILE, index=False)
        enhance_excel_formatting(SALES_FILE)
    
    # Initialize payments file
    if not os.path.exists(PAYMENTS_FILE):
        df = pd.DataFrame(columns=['id', 'type', 'name', 'total_amount', 'paid_amount', 'pending_amount', 
                                 'status', 'payment_date', 'payment_method', 'notes'])
        df.to_excel(PAYMENTS_FILE, index=False)
    
    # Initialize inventory file
    if not os.path.exists(INVENTORY_FILE):
        df = pd.DataFrame(columns=['id', 'description', 'shape', 'carats', 'color', 'clarity', 'cut', 
                                  'purchase_price', 'market_value', 'status', 'location', 'purchase_date', 'notes'])
        df.to_excel(INVENTORY_FILE, index=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buy', methods=['GET', 'POST'])
def buy():
    if request.method == 'POST':
        try:
            # Get form data
            date = request.form.get('date') or None
            party = request.form.get('party') or None
            description = request.form.get('description') or None
            stone_id = request.form.get('stone_id') or None
            rough_id = request.form.get('rough_id') or None
            kapan_no = request.form.get('kapan_no') or None
            platform = request.form.get('platform') or None
            
            # Validate numeric fields
            try:
                carat = float(request.form.get('carat'))
                if carat <= 0:
                    flash('Carat must be greater than 0', 'danger')
                    return redirect(url_for('buy'))
            except (ValueError, TypeError):
                flash('Invalid carat value', 'danger')
                return redirect(url_for('buy'))
            
            try:
                quantity = int(request.form.get('quantity'))
                if quantity <= 0:
                    flash('Quantity must be greater than 0', 'danger')
                    return redirect(url_for('buy'))
            except (ValueError, TypeError):
                flash('Invalid quantity value', 'danger')
                return redirect(url_for('buy'))
            
            try:
                price_per_carat = float(request.form.get('price_per_carat'))
                if price_per_carat <= 0:
                    flash('Price per carat must be greater than 0', 'danger')
                    return redirect(url_for('buy'))
            except (ValueError, TypeError):
                flash('Invalid price per carat value', 'danger')
                return redirect(url_for('buy'))
            
            try:
                price_per_carat_inr = float(request.form.get('price_per_carat_inr'))
                if price_per_carat_inr <= 0:
                    flash('Price per carat (INR) must be greater than 0', 'danger')
                    return redirect(url_for('buy'))
            except (ValueError, TypeError):
                flash('Invalid price per carat (INR) value', 'danger')
                return redirect(url_for('buy'))
            
            # Calculate total amounts
            total_amount_usd = carat * price_per_carat
            total_amount_inr = carat * price_per_carat_inr
            
            # Payment information
            payment_status = request.form.get('payment_status')
            payment_date = request.form.get('payment_date') if payment_status == 'Completed' else None
            payment_reference = request.form.get('payment_reference') or None
            payment_due_date = request.form.get('payment_due_date') or None
            payment_notes = request.form.get('payment_notes') or None
            
            # Initialize partial_payments as None
            partial_payments = None
            
            # Create a new purchase record
            new_purchase = {
                'date': date,
                'party': party,
                'description': description,
                'stone_id': stone_id,
                'rough_id': rough_id,
                'kapan_no': kapan_no,
                'platform': platform,
                'carat': carat,
                'quantity': quantity,
                'price_per_carat': price_per_carat,
                'price_per_carat_inr': price_per_carat_inr,
                'total_amount_usd': total_amount_usd,
                'total_amount_inr': total_amount_inr,
                'payment_status': payment_status,
                'payment_date': payment_date,
                'payment_reference': payment_reference,
                'payment_due_date': payment_due_date,
                'payment_notes': payment_notes,
                'partial_payments': partial_payments
            }
            
            # Load existing purchases or create a new DataFrame
            if os.path.exists(PURCHASES_FILE):
                purchases_df = pd.read_excel(PURCHASES_FILE)
            else:
                purchases_df = pd.DataFrame(columns=list(new_purchase.keys()))
            
            # Append the new purchase
            purchases_df = pd.concat([purchases_df, pd.DataFrame([new_purchase])], ignore_index=True)
            
            # Save the updated DataFrame
            purchases_df.to_excel(PURCHASES_FILE, index=False)
            
            # Create payment record for purchase
            if payment_status != 'Completed':
                try:
                    # Load existing payments or create new DataFrame
                    if os.path.exists(PAYMENTS_FILE):
                        payments_df = pd.read_excel(PAYMENTS_FILE)
                    else:
                        payments_df = pd.DataFrame(columns=['id', 'type', 'name', 'total_amount', 'paid_amount', 
                                                          'pending_amount', 'status', 'payment_date', 
                                                          'payment_method', 'notes', 'reference_id', 'reference_type'])
                    
                    # Generate new payment ID
                    new_id = str(len(payments_df) + 1)
                    
                    # Create payment record
                    new_payment = {
                        'id': new_id,
                        'type': 'supplier',
                        'name': party,
                        'total_amount': total_amount_inr,
                        'paid_amount': 0,
                        'pending_amount': total_amount_inr,
                        'status': 'pending',
                        'payment_date': pd.to_datetime(date),
                        'payment_method': 'pending',
                        'notes': f"Purchase payment for {description}",
                        'reference_id': str(len(purchases_df) - 1),  # Index of the new purchase
                        'reference_type': 'purchase'
                    }
                    
                    # Append new payment
                    payments_df = pd.concat([payments_df, pd.DataFrame([new_payment])], ignore_index=True)
                    payments_df.to_excel(PAYMENTS_FILE, index=False)
                except Exception as e:
                    print(f"Error creating payment record: {str(e)}")
            
            flash('Purchase recorded successfully!', 'success')
            return redirect(url_for('records'))
        
        except Exception as e:
            flash(f'Error recording purchase: {str(e)}', 'danger')
            return redirect(url_for('buy'))
    
    return render_template('buy.html')

@app.route('/sell', methods=['GET', 'POST'])
def sell():
    if request.method == 'POST':
        try:
            # Get form data
            date = request.form.get('date') or None
            party = request.form.get('party') or None
            description = request.form.get('description') or None
            stone_id = request.form.get('stone_id') or None
            rough_id = request.form.get('rough_id') or None
            kapan_no = request.form.get('kapan_no') or None
            platform = request.form.get('platform') or None
            
            # Validate numeric fields
            try:
                carat = float(request.form.get('carat'))
                if carat <= 0:
                    flash('Carat must be greater than 0', 'danger')
                    return redirect(url_for('sell'))
            except (ValueError, TypeError):
                flash('Invalid carat value', 'danger')
                return redirect(url_for('sell'))
            
            try:
                quantity = int(request.form.get('quantity'))
                if quantity <= 0:
                    flash('Quantity must be greater than 0', 'danger')
                    return redirect(url_for('sell'))
            except (ValueError, TypeError):
                flash('Invalid quantity value', 'danger')
                return redirect(url_for('sell'))
            
            try:
                price_per_carat = float(request.form.get('price_per_carat'))
                if price_per_carat <= 0:
                    flash('Price per carat must be greater than 0', 'danger')
                    return redirect(url_for('sell'))
            except (ValueError, TypeError):
                flash('Invalid price per carat value', 'danger')
                return redirect(url_for('sell'))
            
            try:
                price_per_carat_inr = float(request.form.get('price_per_carat_inr'))
                if price_per_carat_inr <= 0:
                    flash('Price per carat (INR) must be greater than 0', 'danger')
                    return redirect(url_for('sell'))
            except (ValueError, TypeError):
                flash('Invalid price per carat (INR) value', 'danger')
                return redirect(url_for('sell'))
            
            # Calculate total amounts
            total_amount_usd = carat * price_per_carat
            total_amount_inr = carat * price_per_carat_inr
            
            # Payment information
            payment_status = request.form.get('payment_status')
            payment_date = request.form.get('payment_date') if payment_status == 'Completed' else None
            payment_reference = request.form.get('payment_reference') or None
            payment_due_date = request.form.get('payment_due_date') or None
            payment_notes = request.form.get('payment_notes') or None
            
            # Initialize partial_payments as None
            partial_payments = None
            
            # Create a new sale record
            new_sale = {
                'date': date,
                'party': party,
                'description': description,
                'stone_id': stone_id,
                'rough_id': rough_id,
                'kapan_no': kapan_no,
                'platform': platform,
                'carat': carat,
                'quantity': quantity,
                'price_per_carat': price_per_carat,
                'price_per_carat_inr': price_per_carat_inr,
                'total_amount_usd': total_amount_usd,
                'total_amount_inr': total_amount_inr,
                'payment_status': payment_status,
                'payment_date': payment_date,
                'payment_reference': payment_reference,
                'payment_due_date': payment_due_date,
                'payment_notes': payment_notes,
                'partial_payments': partial_payments
            }
            
            # Load existing sales or create a new DataFrame
            if os.path.exists(SALES_FILE):
                sales_df = pd.read_excel(SALES_FILE)
            else:
                sales_df = pd.DataFrame(columns=list(new_sale.keys()))
            
            # Append the new sale
            sales_df = pd.concat([sales_df, pd.DataFrame([new_sale])], ignore_index=True)
            
            # Save the updated DataFrame
            sales_df.to_excel(SALES_FILE, index=False)
            
            # Create payment record for sale
            if payment_status != 'Completed':
                try:
                    # Load existing payments or create new DataFrame
                    if os.path.exists(PAYMENTS_FILE):
                        payments_df = pd.read_excel(PAYMENTS_FILE)
                    else:
                        payments_df = pd.DataFrame(columns=['id', 'type', 'name', 'total_amount', 'paid_amount', 
                                                          'pending_amount', 'status', 'payment_date', 
                                                          'payment_method', 'notes', 'reference_id', 'reference_type'])
                    
                    # Generate new payment ID
                    new_id = str(len(payments_df) + 1)
                    
                    # Create payment record
                    new_payment = {
                        'id': new_id,
                        'type': 'customer',
                        'name': party,
                        'total_amount': total_amount_inr,
                        'paid_amount': 0,
                        'pending_amount': total_amount_inr,
                        'status': 'pending',
                        'payment_date': pd.to_datetime(date),
                        'payment_method': 'pending',
                        'notes': f"Sale payment for {description}",
                        'reference_id': str(len(sales_df) - 1),  # Index of the new sale
                        'reference_type': 'sale'
                    }
                    
                    # Append new payment
                    payments_df = pd.concat([payments_df, pd.DataFrame([new_payment])], ignore_index=True)
                    payments_df.to_excel(PAYMENTS_FILE, index=False)
                except Exception as e:
                    print(f"Error creating payment record: {str(e)}")
            
            flash('Sale recorded successfully!', 'success')
            return redirect(url_for('records'))
        
        except Exception as e:
            flash(f'Error recording sale: {str(e)}', 'danger')
            return redirect(url_for('sell'))
    
    return render_template('sell.html')

@app.route('/records')
def records():
    # Load purchase records
    if os.path.exists(PURCHASES_FILE):
        purchases_df = pd.read_excel(PURCHASES_FILE)
        # Replace NaN values with None for proper handling in templates
        purchases_df = purchases_df.replace({pd.NA: None, float('nan'): None})
        purchases = purchases_df.to_dict('records')
    else:
        purchases = []
    
    # Load sales records
    if os.path.exists(SALES_FILE):
        sales_df = pd.read_excel(SALES_FILE)
        # Replace NaN values with None for proper handling in templates
        sales_df = sales_df.replace({pd.NA: None, float('nan'): None})
        sales = sales_df.to_dict('records')
    else:
        sales = []
    
    return render_template('records.html', purchases=purchases, sales=sales)

@app.route('/reports')
def reports():
    """Generate comprehensive business reports and analytics."""
    # Check if the purchases file exists
    if not os.path.exists(PURCHASES_FILE):
        flash('No purchase records found. Please add some purchases first.', 'warning')
        return redirect(url_for('index'))
    
    # Check if the sales file exists
    if not os.path.exists(SALES_FILE):
        flash('No sales records found. Please add some sales first.', 'warning')
        return redirect(url_for('index'))
    
    # Load purchases and sales data
    purchases_df = pd.read_excel(PURCHASES_FILE)
    sales_df = pd.read_excel(SALES_FILE)
    
    try:
        # Calculate basic metrics
        total_purchases = purchases_df['Total Amount USD'].sum() if 'Total Amount USD' in purchases_df.columns else 0
        total_sales = sales_df['Total Amount USD'].sum() if 'Total Amount USD' in sales_df.columns else 0
        profit = total_sales - total_purchases
        
        # Calculate profit percentage - prevent division by zero
        if total_purchases > 0:
            profit_percentage = (profit / total_purchases * 100)
        else:
            profit_percentage = 0
            if profit > 0:
                # If there's profit but no purchases, set to 100%
                profit_percentage = 100
        
        # Calculate volume metrics
        total_carats_purchased = purchases_df['Carat'].sum() if 'Carat' in purchases_df.columns else 0
        total_carats_sold = sales_df['Carat'].sum() if 'Carat' in sales_df.columns else 0
        
        # Calculate average prices - prevent division by zero
        if total_carats_purchased > 0:
            avg_purchase_price = total_purchases / total_carats_purchased
        else:
            avg_purchase_price = 0
            
        if total_carats_sold > 0:
            avg_sale_price = total_sales / total_carats_sold
        else:
            avg_sale_price = 0
        
        # Count transactions
        purchase_count = len(purchases_df)
        sales_count = len(sales_df)
        
        # Prepare report data
        report_data = {
            'total_purchases': total_purchases,
            'total_sales': total_sales,
            'profit': profit,
            'profit_percentage': profit_percentage,
            'total_carats_purchased': total_carats_purchased,
            'total_carats_sold': total_carats_sold,
            'avg_purchase_price': avg_purchase_price,
            'avg_sale_price': avg_sale_price,
            'purchase_count': purchase_count,
            'sales_count': sales_count
        }
    except Exception as e:
        flash(f'Error generating reports: {str(e)}', 'danger')
        # Provide default values for the report data
        report_data = {
            'total_purchases': 0,
            'total_sales': 0,
            'profit': 0,
            'profit_percentage': 0,
            'total_carats_purchased': 0,
            'total_carats_sold': 0,
            'avg_purchase_price': 0,
            'avg_sale_price': 0,
            'purchase_count': 0,
            'sales_count': 0
        }
    
    return render_template('reports.html', report_data=report_data)

@app.route('/dashboard')
def dashboard():
    # Check if the purchases file exists
    if not os.path.exists(PURCHASES_FILE):
        flash('No purchase records found. Please add some purchases first.', 'warning')
        return redirect(url_for('index'))
    
    # Check if the sales file exists
    if not os.path.exists(SALES_FILE):
        flash('No sales records found. Please add some sales first.', 'warning')
        return redirect(url_for('index'))
    
    # Load purchases and sales data
    try:
        purchases_df = pd.read_excel(PURCHASES_FILE)
        sales_df = pd.read_excel(SALES_FILE)
    except Exception as e:
        flash(f'Error loading Excel files: {str(e)}', 'danger')
        return redirect(url_for('index'))
    
    # Calculate totals - handle different column name formats
    try:
        # Try different possible column names for total amount
        if 'Total Amount USD' in purchases_df.columns:
            total_purchases = purchases_df['Total Amount USD'].sum()
        elif 'Total Amount (USD)' in purchases_df.columns:
            total_purchases = purchases_df['Total Amount (USD)'].sum()
        elif 'Total Amount' in purchases_df.columns:
            total_purchases = purchases_df['Total Amount'].sum()
        else:
            # If no matching column is found, use 0
            flash('Warning: Could not find total amount column in purchases file', 'warning')
            total_purchases = 0
        
        if 'Total Amount USD' in sales_df.columns:
            total_sales = sales_df['Total Amount USD'].sum()
        elif 'Total Amount (USD)' in sales_df.columns:
            total_sales = sales_df['Total Amount (USD)'].sum()
        elif 'Total Amount' in sales_df.columns:
            total_sales = sales_df['Total Amount'].sum()
        else:
            # If no matching column is found, use 0
            flash('Warning: Could not find total amount column in sales file', 'warning')
            total_sales = 0
        
        profit = total_sales - total_purchases
        
        # Calculate profit percentage with safe division
        if total_purchases > 0:
            profit_percentage = (profit / total_purchases) * 100
        else:
            # Handle division by zero
            if profit > 0:
                # If there's profit but no purchases, set to 100%
                profit_percentage = 100
            elif profit < 0:
                # If there's loss but no purchases, set to -100%
                profit_percentage = -100
            else:
                # If no profit and no purchases, set to 0%
                profit_percentage = 0
        
        # Calculate volume metrics
        if 'Carat' in purchases_df.columns:
            total_carats_purchased = purchases_df['Carat'].sum()
        else:
            total_carats_purchased = 0
            
        if 'Carat' in sales_df.columns:
            total_carats_sold = sales_df['Carat'].sum()
        else:
            total_carats_sold = 0
            
        # Count transactions
        purchase_count = len(purchases_df)
        sales_count = len(sales_df)
        
        # Calculate total pieces
        total_pcs_purchased = purchases_df['Pcs'].sum() if 'Pcs' in purchases_df.columns else 0
        total_pcs_sold = sales_df['Pcs'].sum() if 'Pcs' in sales_df.columns else 0
        
        # Count payment statuses for purchases
        if 'Payment Status' in purchases_df.columns:
            completed_purchase_count = len(purchases_df[purchases_df['Payment Status'] == 'Completed'])
            pending_purchase_count = len(purchases_df[purchases_df['Payment Status'] == 'Pending'])
            partial_purchase_count = len(purchases_df[purchases_df['Payment Status'] == 'Partial'])
        else:
            completed_purchase_count = 0
            pending_purchase_count = 0
            partial_purchase_count = 0
        
        # Count payment statuses for sales
        if 'Payment Status' in sales_df.columns:
            completed_sale_count = len(sales_df[sales_df['Payment Status'] == 'Completed'])
            pending_sale_count = len(sales_df[sales_df['Payment Status'] == 'Pending'])
            partial_sale_count = len(sales_df[sales_df['Payment Status'] == 'Partial'])
        else:
            completed_sale_count = 0
            pending_sale_count = 0
            partial_sale_count = 0
        
    except Exception as e:
        flash(f'Error calculating dashboard metrics: {str(e)}', 'danger')
        total_purchases = 0
        total_sales = 0
        profit = 0
        profit_percentage = 0
        total_carats_purchased = 0
        total_carats_sold = 0
        purchase_count = 0
        sales_count = 0
        total_pcs_purchased = 0
        total_pcs_sold = 0
        completed_purchase_count = 0
        pending_purchase_count = 0
        partial_purchase_count = 0
        completed_sale_count = 0
        pending_sale_count = 0
        partial_sale_count = 0
    
    return render_template('dashboard.html', 
                           total_purchases=total_purchases,
                           total_sales=total_sales,
                           profit=profit,
                           profit_percentage=profit_percentage,
                           total_carats_purchased=total_carats_purchased,
                           total_carats_sold=total_carats_sold,
                           purchase_count=purchase_count,
                           sales_count=sales_count,
                           total_pcs_purchased=total_pcs_purchased,
                           total_pcs_sold=total_pcs_sold,
                           completed_purchase_count=completed_purchase_count,
                           pending_purchase_count=pending_purchase_count,
                           partial_purchase_count=partial_purchase_count,
                           completed_sale_count=completed_sale_count,
                           pending_sale_count=pending_sale_count,
                           partial_sale_count=partial_sale_count)

@app.route('/delete_record', methods=['POST'])
def delete_record():
    record_type = request.form.get('record_type')
    record_index = request.form.get('record_index')
    
    if not record_type or not record_index:
        flash('Invalid request', 'danger')
        return redirect(url_for('records'))
    
    try:
        record_index = int(record_index)
        
        if record_type == 'purchase':
            file_path = PURCHASES_FILE
        elif record_type == 'sale':
            file_path = SALES_FILE
        else:
            flash('Invalid record type', 'danger')
            return redirect(url_for('records'))
        
        # Load the data
        if not os.path.exists(file_path):
            flash('Record file not found', 'danger')
            return redirect(url_for('records'))
        
        df = pd.read_excel(file_path)
        
        if record_index < 0 or record_index >= len(df):
            flash('Record not found', 'danger')
            return redirect(url_for('records'))
        
        # Delete the record
        df = df.drop(record_index).reset_index(drop=True)
        
        # Save the updated dataframe
        df.to_excel(file_path, index=False)
        enhance_excel_formatting(file_path)
        
        flash('Record deleted successfully!', 'success')
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('records'))

@app.route('/export/<file_type>')
def export(file_type):
    try:
        if file_type == 'purchases':
            source_file = PURCHASES_FILE
            filename = 'diamond_purchases.xlsx'
        elif file_type == 'sales':
            source_file = SALES_FILE
            filename = 'diamond_sales.xlsx'
        else:
            flash('Invalid file type', 'danger')
            return redirect(url_for('records'))
        
        # Ensure the source file exists
        if not os.path.exists(source_file):
            flash(f'Source file not found: {source_file}', 'danger')
            return redirect(url_for('records'))
        
        # Create a temporary directory if it doesn't exist
        temp_dir = os.path.join(DATA_DIR, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Create a unique temporary file path
        temp_file = os.path.join(temp_dir, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}")
        
        # Read the source file with pandas
        try:
            df = pd.read_excel(source_file)
            
            # Write to the temporary file
            with pd.ExcelWriter(temp_file, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
                
            # Enhance the Excel file after it's been properly saved
            enhance_excel_formatting(temp_file)
            
            # Send the file to the user
            return send_file(
                temp_file,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        except Exception as e:
            # If there's an error with pandas, try a direct file copy
            import shutil
            shutil.copy2(source_file, temp_file)
            
            # Send the file to the user without enhancement
            flash(f'Warning: Could not enhance the Excel file. Sending original format.', 'warning')
            return send_file(
                temp_file,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
    except Exception as e:
        flash(f'Error exporting file: {str(e)}', 'danger')
        return redirect(url_for('records'))

@app.route('/debug_excel')
def debug_excel():
    """Debug route to display Excel file information."""
    try:
        purchases_info = {}
        sales_info = {}
        
        if os.path.exists(PURCHASES_FILE):
            purchases_df = pd.read_excel(PURCHASES_FILE)
            purchases_info = {
                'exists': True,
                'columns': list(purchases_df.columns),
                'row_count': len(purchases_df),
                'file_path': PURCHASES_FILE
            }
        else:
            purchases_info = {
                'exists': False,
                'file_path': PURCHASES_FILE
            }
            
        if os.path.exists(SALES_FILE):
            sales_df = pd.read_excel(SALES_FILE)
            sales_info = {
                'exists': True,
                'columns': list(sales_df.columns),
                'row_count': len(sales_df),
                'file_path': SALES_FILE
            }
        else:
            sales_info = {
                'exists': False,
                'file_path': SALES_FILE
            }
            
        return render_template('debug_excel.html', 
                              purchases_info=purchases_info,
                              sales_info=sales_info)
    except Exception as e:
        return f"""
        <h1>Excel Debug Information</h1>
        <p style="color: red;">Error: {str(e)}</p>
        <p>Purchases file path: {PURCHASES_FILE}</p>
        <p>Sales file path: {SALES_FILE}</p>
        """

@app.route('/reinitialize_excel', methods=['GET', 'POST'])
def reinitialize_excel():
    if request.method == 'POST':
        try:
            # Create backup directory if it doesn't exist
            backup_dir = os.path.join(DATA_DIR, 'backup')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup existing files if they exist
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if os.path.exists(PURCHASES_FILE):
                backup_file = os.path.join(backup_dir, f'purchases_backup_{timestamp}.xlsx')
                import shutil
                shutil.copy2(PURCHASES_FILE, backup_file)
                flash(f'Backed up purchases file to {backup_file}', 'info')
            
            if os.path.exists(SALES_FILE):
                backup_file = os.path.join(backup_dir, f'sales_backup_{timestamp}.xlsx')
                import shutil
                shutil.copy2(SALES_FILE, backup_file)
                flash(f'Backed up sales file to {backup_file}', 'info')
            
            # Create new purchases file
            purchases_df = pd.DataFrame(columns=[
                'Date', 'Party', 'Description', 'Stone ID', 'Rough ID', 'Kapan No', 'Platform',
                'Carat', 'Than', 'Pcs', 'Price Per Carat', 'Price Per Carat INR', 'Rate', 'Total Amount USD', 'Total Amount INR',
                'Payment Status', 'Reference Party', 'Payment Due Date', 'Payment Days', 'Payment Done Date', 'Notes'
            ])
            purchases_df.to_excel(PURCHASES_FILE, index=False)
            
            # Create new sales file
            sales_df = pd.DataFrame(columns=[
                'Date', 'Party', 'Description', 'Stone ID', 'Rough ID', 'Kapan No', 'Platform',
                'Carat', 'Than', 'Pcs', 'Price Per Carat', 'Price Per Carat INR', 'Rate', 'Total Amount USD', 'Total Amount INR',
                'Payment Status', 'Reference Party', 'Payment Due Date', 'Payment Days', 'Payment Done Date', 'Notes'
            ])
            sales_df.to_excel(SALES_FILE, index=False)
            
            # Apply formatting
            enhance_excel_formatting(PURCHASES_FILE)
            enhance_excel_formatting(SALES_FILE)
            
            flash('Excel files have been reinitialized successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error reinitializing Excel files: {str(e)}', 'danger')
            return redirect(url_for('reinitialize_excel'))
    
    return render_template('reinitialize_confirm.html')

@app.route('/edit_record/<record_type>/<int:record_index>', methods=['GET', 'POST'])
def edit_record(record_type, record_index):
    if record_type not in ['purchase', 'sale']:
        flash('Invalid record type.', 'danger')
        return redirect(url_for('records'))
    
    file_path = PURCHASES_FILE if record_type == 'purchase' else SALES_FILE
    
    if not os.path.exists(file_path):
        flash(f'No {record_type} records found.', 'danger')
        return redirect(url_for('records'))
    
    try:
        df = pd.read_excel(file_path)
        df = df.replace({pd.NA: None, float('nan'): None})
        
        if record_index < 0 or record_index >= len(df):
            flash('Invalid record index.', 'danger')
            return redirect(url_for('records'))
        
        if request.method == 'POST':
            try:
                # Get form data
                date = request.form.get('date') or None
                party = request.form.get('party') or None
                description = request.form.get('description') or None
                stone_id = request.form.get('stone_id') or None
                rough_id = request.form.get('rough_id') or None
                kapan_no = request.form.get('kapan_no') or None
                platform = request.form.get('platform') or None
                
                # Validate numeric fields
                try:
                    carat = float(request.form.get('carat'))
                    if carat <= 0:
                        flash('Carat must be greater than 0', 'danger')
                        return redirect(url_for('edit_record', record_type=record_type, record_index=record_index))
                except (ValueError, TypeError):
                    flash('Invalid carat value', 'danger')
                    return redirect(url_for('edit_record', record_type=record_type, record_index=record_index))
                
                try:
                    quantity = int(request.form.get('quantity'))
                    if quantity <= 0:
                        flash('Quantity must be greater than 0', 'danger')
                        return redirect(url_for('edit_record', record_type=record_type, record_index=record_index))
                except (ValueError, TypeError):
                    flash('Invalid quantity value', 'danger')
                    return redirect(url_for('edit_record', record_type=record_type, record_index=record_index))
                
                try:
                    price_per_carat = float(request.form.get('price_per_carat'))
                    if price_per_carat <= 0:
                        flash('Price per carat must be greater than 0', 'danger')
                        return redirect(url_for('edit_record', record_type=record_type, record_index=record_index))
                except (ValueError, TypeError):
                    flash('Invalid price per carat value', 'danger')
                    return redirect(url_for('edit_record', record_type=record_type, record_index=record_index))
                
                try:
                    price_per_carat_inr = float(request.form.get('price_per_carat_inr'))
                    if price_per_carat_inr <= 0:
                        flash('Price per carat (INR) must be greater than 0', 'danger')
                        return redirect(url_for('edit_record', record_type=record_type, record_index=record_index))
                except (ValueError, TypeError):
                    flash('Invalid price per carat (INR) value', 'danger')
                    return redirect(url_for('edit_record', record_type=record_type, record_index=record_index))
                
                # Calculate total amounts
                total_amount_usd = carat * price_per_carat
                total_amount_inr = carat * price_per_carat_inr
                
                # Payment information
                payment_status = request.form.get('payment_status')
                payment_date = request.form.get('payment_date') if payment_status == 'Completed' else None
                payment_reference = request.form.get('payment_reference') or None
                payment_due_date = request.form.get('payment_due_date') or None
                payment_notes = request.form.get('payment_notes') or None
                
                # Preserve existing partial payments
                partial_payments = df.at[record_index, 'partial_payments']
                
                # Update record
                df.at[record_index, 'Date'] = date
                df.at[record_index, 'Party'] = party
                df.at[record_index, 'Description'] = description
                df.at[record_index, 'Stone ID'] = stone_id
                df.at[record_index, 'Rough ID'] = rough_id
                df.at[record_index, 'Kapan No'] = kapan_no
                df.at[record_index, 'Platform'] = platform
                df.at[record_index, 'Carat'] = carat
                df.at[record_index, 'Quantity'] = quantity
                df.at[record_index, 'Price Per Carat'] = price_per_carat
                df.at[record_index, 'Price Per Carat INR'] = price_per_carat_inr
                df.at[record_index, 'Total Amount USD'] = total_amount_usd
                df.at[record_index, 'Total Amount INR'] = total_amount_inr
                df.at[record_index, 'Payment Status'] = payment_status
                df.at[record_index, 'Payment Done Date'] = payment_date
                df.at[record_index, 'Reference Party'] = payment_reference
                df.at[record_index, 'Payment Due Date'] = payment_due_date
                df.at[record_index, 'Notes'] = payment_notes
                
                # If status is not Partial, clear partial payments
                if payment_status != 'Partial':
                    df.at[record_index, 'partial_payments'] = None
                else:
                    # Keep existing partial payments
                    df.at[record_index, 'partial_payments'] = partial_payments
                
                # Save the updated DataFrame
                df.to_excel(file_path, index=False)
                
                flash(f'{record_type.capitalize()} record updated successfully!', 'success')
                return redirect(url_for('records'))
            
            except Exception as e:
                flash(f'Error updating record: {str(e)}', 'danger')
                return redirect(url_for('edit_record', record_type=record_type, record_index=record_index))
        
        # GET request - display the form with current values
        record = df.iloc[record_index].to_dict()
        
        # Use the appropriate template based on record type
        template_name = f'edit_{record_type}.html'
        
        return render_template(
            template_name,
            record=record,
            record_type=record_type,
            record_index=record_index
        )
    
    except Exception as e:
        flash(f'Error loading record: {str(e)}', 'danger')
        return redirect(url_for('records'))

@app.route('/backup')
def backup():
    """Create a backup of all data files."""
    try:
        # Create backup directory if it doesn't exist
        backup_dir = os.path.join(DATA_DIR, 'backup')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create a timestamp for the backup files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create a zip file for the backup
        import zipfile
        zip_filename = f'diamond_data_backup_{timestamp}.zip'
        zip_path = os.path.join(backup_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # Add purchases file if it exists
            if os.path.exists(PURCHASES_FILE):
                zipf.write(PURCHASES_FILE, os.path.basename(PURCHASES_FILE))
            
            # Add sales file if it exists
            if os.path.exists(SALES_FILE):
                zipf.write(SALES_FILE, os.path.basename(SALES_FILE))
        
        # Send the zip file to the user
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=zip_filename,
            mimetype='application/zip'
        )
    except Exception as e:
        flash(f'Error creating backup: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/restore', methods=['GET', 'POST'])
def restore():
    """Restore data from a backup file."""
    if request.method == 'POST':
        try:
            # Check if a file was uploaded
            if 'backup_file' not in request.files:
                flash('No backup file selected', 'danger')
                return redirect(url_for('restore'))
            
            backup_file = request.files['backup_file']
            
            # Check if the file has a name
            if backup_file.filename == '':
                flash('No backup file selected', 'danger')
                return redirect(url_for('restore'))
            
            # Check if the file is a zip file
            if not backup_file.filename.endswith('.zip'):
                flash('Backup file must be a zip file', 'danger')
                return redirect(url_for('restore'))
            
            # Create a temporary directory for extraction
            import tempfile
            import zipfile
            import shutil
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save the uploaded file to the temporary directory
                backup_path = os.path.join(temp_dir, 'backup.zip')
                backup_file.save(backup_path)
                
                # Extract the zip file
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # Create backup of current files before restoring
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_dir = os.path.join(DATA_DIR, 'backup')
                os.makedirs(backup_dir, exist_ok=True)
                
                if os.path.exists(PURCHASES_FILE):
                    backup_purchases = os.path.join(backup_dir, f'purchases_before_restore_{timestamp}.xlsx')
                    shutil.copy2(PURCHASES_FILE, backup_purchases)
                
                if os.path.exists(SALES_FILE):
                    backup_sales = os.path.join(backup_dir, f'sales_before_restore_{timestamp}.xlsx')
                    shutil.copy2(SALES_FILE, backup_sales)
                
                # Restore the files
                extracted_purchases = os.path.join(temp_dir, os.path.basename(PURCHASES_FILE))
                extracted_sales = os.path.join(temp_dir, os.path.basename(SALES_FILE))
                
                if os.path.exists(extracted_purchases):
                    shutil.copy2(extracted_purchases, PURCHASES_FILE)
                    enhance_excel_formatting(PURCHASES_FILE)
                
                if os.path.exists(extracted_sales):
                    shutil.copy2(extracted_sales, SALES_FILE)
                    enhance_excel_formatting(SALES_FILE)
                
                flash('Data restored successfully!', 'success')
                return redirect(url_for('index'))
                
        except Exception as e:
            flash(f'Error restoring backup: {str(e)}', 'danger')
            return redirect(url_for('restore'))
    
    return render_template('restore.html')

@app.route('/update_payment_status', methods=['POST'])
def update_payment_status():
    record_type = request.form.get('record_type')
    record_index = request.form.get('record_index')
    new_status = request.form.get('payment_status')
    payment_done_date = request.form.get('payment_done_date')
    total_amount_inr = request.form.get('total_amount_inr')
    original_exchange_rate = request.form.get('original_exchange_rate')
    security_hash = request.form.get('security_hash')
    
    # For partial payments
    partial_amount = request.form.get('partial_amount')
    partial_payment_date = request.form.get('partial_payment_date')
    partial_payment_reference = request.form.get('partial_payment_reference')
    payment_currency = request.form.get('payment_currency', 'INR')  # Default to INR
    
    try:
        record_index = int(record_index)
        
        if record_type not in ['purchase', 'sale']:
            flash('Invalid record type.', 'danger')
            return redirect(url_for('records'))
        
        file_path = PURCHASES_FILE if record_type == 'purchase' else SALES_FILE
        
        if not os.path.exists(file_path):
            flash(f'No {record_type} records found.', 'danger')
            return redirect(url_for('records'))
        
        df = pd.read_excel(file_path)
        
        if record_index < 0 or record_index >= len(df):
            flash('Invalid record index.', 'danger')
            return redirect(url_for('records'))
        
        # Security check: Verify the total amount hasn't been tampered with
        stored_total_inr = df.at[record_index, 'Total Amount INR']
        if total_amount_inr and abs(float(total_amount_inr) - float(stored_total_inr)) > 0.01:
            flash('Security warning: Total amount mismatch detected.', 'danger')
            return redirect(url_for('records'))
        
        # Security check: Verify the security hash
        if security_hash:
            expected_hash = generate_security_hash(stored_total_inr)
            if security_hash != expected_hash:
                flash('Security warning: Data integrity check failed.', 'danger')
                return redirect(url_for('records'))
        
        # Get the original exchange rate from the record
        stored_rate = df.at[record_index, 'Rate']
        if not original_exchange_rate or abs(float(original_exchange_rate) - float(stored_rate)) > 0.01:
            # Use the stored rate if there's a mismatch
            exchange_rate = stored_rate
        else:
            exchange_rate = original_exchange_rate
        
        # Update payment status
        df.at[record_index, 'Payment Status'] = new_status
        
        # Handle different payment status types
        if new_status == 'Completed':
            # For completed payments, update the payment date
            if payment_done_date:
                df.at[record_index, 'Payment Done Date'] = payment_done_date
            
            # Clear partial payments if any (convert to completed)
            df.at[record_index, 'partial_payments'] = None
            
        elif new_status == 'Partial':
            # For partial payments, add to the payment history
            if partial_amount and partial_payment_date:
                try:
                    partial_amount = float(partial_amount)
                    exchange_rate = float(exchange_rate)
                    
                    # Get existing partial payments or create new list
                    partial_payments = []
                    if pd.notna(df.at[record_index, 'partial_payments']) and df.at[record_index, 'partial_payments']:
                        try:
                            partial_payments = json.loads(df.at[record_index, 'partial_payments'])
                        except:
                            partial_payments = []
                    
                    # Add new payment with currency information
                    new_payment = {
                        'date': partial_payment_date,
                        'amount': partial_amount,
                        'currency': payment_currency,
                        'exchange_rate': exchange_rate,  # Always use the original exchange rate
                        'reference': partial_payment_reference or ''
                    }
                    partial_payments.append(new_payment)
                    
                    # Store as JSON string
                    df.at[record_index, 'partial_payments'] = json.dumps(partial_payments)
                    
                    # Calculate total received in both currencies
                    total_received_usd = 0
                    total_received_inr = 0
                    
                    for payment in partial_payments:
                        payment_amount = float(payment['amount'])
                        # Always use the original exchange rate for consistency
                        payment_rate = float(exchange_rate)
                        
                        if payment.get('currency') == 'INR':
                            # For INR payments
                            total_received_inr += payment_amount
                            total_received_usd += payment_amount / payment_rate
                        else:
                            # For USD payments
                            total_received_usd += payment_amount
                            total_received_inr += payment_amount * payment_rate
                    
                    # Check if fully paid (based on INR amount)
                    total_amount_inr = df.at[record_index, 'Total Amount INR']
                    
                    # If received amount is within 1 rupee of total, consider it fully paid
                    if abs(total_received_inr - total_amount_inr) <= 1.0:
                        df.at[record_index, 'Payment Status'] = 'Completed'
                        df.at[record_index, 'Payment Done Date'] = partial_payment_date
                        
                except ValueError:
                    flash('Invalid payment amount or exchange rate.', 'danger')
                    return redirect(url_for('records'))
            else:
                flash('Payment amount and date are required for partial payments.', 'danger')
                return redirect(url_for('records'))
        else:
            # For pending or other statuses, clear payment date
            df.at[record_index, 'Payment Done Date'] = None
            df.at[record_index, 'partial_payments'] = None
        
        # Save the updated DataFrame
        df.to_excel(file_path, index=False)
        
        flash(f'{record_type.capitalize()} payment status updated successfully.', 'success')
        return redirect(url_for('records'))
    
    except Exception as e:
        flash(f'Error updating payment status: {str(e)}', 'danger')
        return redirect(url_for('records'))

@app.route('/get_record_details')
def get_record_details():
    record_type = request.args.get('record_type')
    record_index = request.args.get('record_index')
    
    try:
        record_index = int(record_index)
        
        if record_type not in ['purchase', 'sale']:
            return jsonify({'error': 'Invalid record type'}), 400
        
        file_path = PURCHASES_FILE if record_type == 'purchase' else SALES_FILE
        
        if not os.path.exists(file_path):
            return jsonify({'error': f'No {record_type} records found'}), 404
        
        df = pd.read_excel(file_path)
        
        if record_index < 0 or record_index >= len(df):
            return jsonify({'error': 'Invalid record index'}), 400
        
        # Get record details
        record = df.iloc[record_index].replace({pd.NA: None, float('nan'): None})
        
        # Convert to dictionary
        record_dict = record.to_dict()
        
        # Parse partial payments if they exist
        if 'partial_payments' in record_dict and record_dict['partial_payments']:
            try:
                if isinstance(record_dict['partial_payments'], str):
                    record_dict['partial_payments'] = json.loads(record_dict['partial_payments'])
                else:
                    record_dict['partial_payments'] = []
            except:
                record_dict['partial_payments'] = []
        else:
            record_dict['partial_payments'] = []
        
        # Ensure all required fields exist
        if 'Total Amount USD' not in record_dict:
            record_dict['Total Amount USD'] = record_dict.get('Total Amount', 0)
        
        if 'Total Amount INR' not in record_dict:
            # Calculate INR amount if not present
            if 'Rate' in record_dict and record_dict['Rate'] and record_dict['Rate'] is not None and 'Total Amount USD' in record_dict:
                try:
                    rate = float(record_dict['Rate'])
                    total_usd = float(record_dict['Total Amount USD'])
                    record_dict['Total Amount INR'] = total_usd * rate
                except (ValueError, TypeError):
                    record_dict['Total Amount INR'] = 0
            else:
                record_dict['Total Amount INR'] = 0
        
        # Ensure Rate is present
        if 'Rate' not in record_dict or not record_dict['Rate']:
            record_dict['Rate'] = 83.50  # Default rate
        
        # Calculate received amounts in both currencies using the original rate
        total_received_usd = 0
        total_received_inr = 0
        original_rate = float(record_dict['Rate'])
        
        if record_dict['partial_payments']:
            for payment in record_dict['partial_payments']:
                payment_amount = float(payment['amount'])
                
                # Always use the original exchange rate for consistency
                if payment.get('currency') == 'INR':
                    # For INR payments
                    total_received_inr += payment_amount
                    total_received_usd += payment_amount / original_rate
                else:
                    # For USD payments
                    total_received_usd += payment_amount
                    total_received_inr += payment_amount * original_rate
                
                # Ensure the payment has the original exchange rate
                payment['exchange_rate'] = original_rate
        
        # Add received amounts to the response
        record_dict['received_amount_usd'] = total_received_usd
        record_dict['received_amount_inr'] = total_received_inr
        record_dict['remaining_amount_usd'] = max(0, float(record_dict['Total Amount USD']) - total_received_usd)
        record_dict['remaining_amount_inr'] = max(0, float(record_dict['Total Amount INR']) - total_received_inr)
        
        # Convert numeric values to proper format
        for key in record_dict:
            if key in ['Total Amount USD', 'Total Amount INR', 'Rate', 
                      'received_amount_usd', 'received_amount_inr', 
                      'remaining_amount_usd', 'remaining_amount_inr']:
                try:
                    if record_dict[key] is not None:
                        record_dict[key] = float(record_dict[key])
                except (ValueError, TypeError):
                    record_dict[key] = 0
        
        # Add a security hash to prevent tampering with total amounts
        record_dict['security_hash'] = generate_security_hash(record_dict['Total Amount INR'])
        
        # Add a flag indicating the rate is locked
        record_dict['rate_locked'] = True
        
        return jsonify(record_dict)
    
    except Exception as e:
        app.logger.error(f"Error in get_record_details: {str(e)}")
        return jsonify({'error': str(e)}), 500

def generate_security_hash(amount):
    """Generate a simple hash for security verification of amount"""
    if amount is None:
        return ""
    # Use a simple hash for demonstration - in production, use a proper cryptographic approach
    amount_str = str(float(amount))
    return hashlib.md5((amount_str + app.secret_key).encode()).hexdigest()[:10]

# Function to format currency
def format_currency(value):
    try:
        return "{:,.2f}".format(float(value))
    except (ValueError, TypeError):
        return "0.00"

# Add the format_currency filter to Jinja2
app.jinja_env.filters['format_currency'] = format_currency

def get_payment_status_color(status):
    status_colors = {
        'pending': 'danger',
        'partial': 'warning',
        'completed': 'success'
    }
    return status_colors.get(status.lower(), 'secondary')

@app.route('/payments')
def payments():
    try:
        # Load payments data
        if os.path.exists(PAYMENTS_FILE):
            payments_df = pd.read_excel(PAYMENTS_FILE)
        else:
            payments_df = pd.DataFrame(columns=['id', 'type', 'name', 'total_amount', 'paid_amount', 'pending_amount', 
                                     'status', 'payment_date', 'payment_method', 'notes'])
            payments_df.to_excel(PAYMENTS_FILE, index=False)

        # Load purchases and sales data
        purchases_df = pd.read_excel(PURCHASES_FILE) if os.path.exists(PURCHASES_FILE) else pd.DataFrame()
        sales_df = pd.read_excel(SALES_FILE) if os.path.exists(SALES_FILE) else pd.DataFrame()

        # Calculate totals
        total_pending = payments_df['pending_amount'].sum() if not payments_df.empty else 0
        total_received = payments_df['paid_amount'].sum() if not payments_df.empty else 0
        total_purchases = purchases_df['Total Amount INR'].sum() if not purchases_df.empty else 0
        total_sales = sales_df['Total Amount INR'].sum() if not sales_df.empty else 0

        # Apply filters if provided
        status = request.args.get('status')
        type_filter = request.args.get('type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Prepare transactions list
        transactions = []

        # Safely convert a date with full NaT handling
        def safe_date_convert(date_value):
            if pd.isna(date_value):
                return pd.Timestamp.now(), "00:00"
            
            try:
                date_obj = pd.to_datetime(date_value)
                if pd.isna(date_obj):
                    return pd.Timestamp.now(), "00:00"
                return date_obj, date_obj.strftime('%H:%M')
            except:
                return pd.Timestamp.now(), "00:00"

        # Add purchases to transactions
        if not purchases_df.empty:
            for _, row in purchases_df.iterrows():
                # Safely handle all potential NaT/NaN values
                date_value, time_str = safe_date_convert(row.get('Date'))
                status_value = str(row.get('Payment Status', "Unknown")) if pd.notna(row.get('Payment Status')) else "Unknown"
                party_value = str(row.get('Party', "Unknown")) if pd.notna(row.get('Party')) else "Unknown"
                
                try:
                    amount = float(row.get('Total Amount INR', 0))
                except:
                    amount = 0
                
                transaction = {
                    'date': date_value,
                    'time': time_str,
                    'type': 'purchase',
                    'party': party_value,
                    'amount': amount,
                    'status': status_value,
                    'status_color': get_payment_status_color(status_value),
                    'id': str(row.name)  # Use index as ID
                }
                transactions.append(transaction)

        # Add sales to transactions
        if not sales_df.empty:
            for _, row in sales_df.iterrows():
                # Safely handle all potential NaT/NaN values
                date_value, time_str = safe_date_convert(row.get('Date'))
                status_value = str(row.get('Payment Status', "Unknown")) if pd.notna(row.get('Payment Status')) else "Unknown"
                party_value = str(row.get('Party', "Unknown")) if pd.notna(row.get('Party')) else "Unknown"
                
                try:
                    amount = float(row.get('Total Amount INR', 0))
                except:
                    amount = 0
                
                transaction = {
                    'date': date_value,
                    'time': time_str,
                    'type': 'sale',
                    'party': party_value,
                    'amount': amount,
                    'status': status_value,
                    'status_color': get_payment_status_color(status_value),
                    'id': str(row.name)  # Use index as ID
                }
                transactions.append(transaction)

        # Add payments to transactions
        if not payments_df.empty:
            for _, row in payments_df.iterrows():
                # Safely handle all potential NaT/NaN values
                date_value, time_str = safe_date_convert(row.get('payment_date'))
                status_value = str(row.get('status', "Unknown")) if pd.notna(row.get('status')) else "Unknown"
                name_value = str(row.get('name', "Unknown")) if pd.notna(row.get('name')) else "Unknown"
                
                try:
                    amount = float(row.get('total_amount', 0))
                except:
                    amount = 0
                
                transaction = {
                    'date': date_value,
                    'time': time_str,
                    'type': 'payment',
                    'party': name_value,
                    'amount': amount,
                    'status': status_value,
                    'status_color': get_payment_status_color(status_value),
                    'id': str(row.get('id', row.name))
                }
                transactions.append(transaction)

        # Sort transactions by date (newest first)
        transactions.sort(key=lambda x: x['date'], reverse=True)

        # Apply filters to transactions
        if status:
            transactions = [t for t in transactions if isinstance(t['status'], str) and t['status'].lower() == status.lower()]
        if type_filter:
            transactions = [t for t in transactions if t['type'] == type_filter]
        if start_date:
            try:
                start_date = pd.to_datetime(start_date)
                transactions = [t for t in transactions if t['date'] >= start_date]
            except:
                pass  # Ignore invalid start date
        if end_date:
            try:
                end_date = pd.to_datetime(end_date)
                transactions = [t for t in transactions if t['date'] <= end_date]
            except:
                pass  # Ignore invalid end date

        # Prepare pending payments list from both purchases and sales
        pending_payments = []

        # Add pending purchases
        if not purchases_df.empty:
            for _, row in purchases_df.iterrows():
                # Check if payment status is pending or partial (case insensitive)
                status_value = str(row.get('Payment Status', "")).lower() if pd.notna(row.get('Payment Status')) else ""
                if status_value not in ['pending', 'partial']:
                    continue
                
                # Safely get date
                date_value, _ = safe_date_convert(row.get('Date'))
                
                # Ensure values are of proper type
                formatted_status = str(row.get('Payment Status', "Unknown")) if pd.notna(row.get('Payment Status')) else "Unknown"
                party_value = str(row.get('Party', "Unknown")) if pd.notna(row.get('Party')) else "Unknown"
                
                try:
                    amount = float(row.get('Total Amount INR', 0))
                except:
                    amount = 0
                
                payment = {
                    'id': str(row.name),
                    'type': 'supplier',
                    'name': party_value,
                    'total_amount': amount,
                    'pending_amount': amount,
                    'status': formatted_status,
                    'status_color': get_payment_status_color(formatted_status),
                    'reference_type': 'purchase',
                    'date': date_value
                }
                pending_payments.append(payment)

        # Add pending sales
        if not sales_df.empty:
            for _, row in sales_df.iterrows():
                # Check if payment status is pending or partial (case insensitive)
                status_value = str(row.get('Payment Status', "")).lower() if pd.notna(row.get('Payment Status')) else ""
                if status_value not in ['pending', 'partial']:
                    continue
                
                # Safely get date
                date_value, _ = safe_date_convert(row.get('Date'))
                
                # Ensure values are of proper type
                formatted_status = str(row.get('Payment Status', "Unknown")) if pd.notna(row.get('Payment Status')) else "Unknown"
                party_value = str(row.get('Party', "Unknown")) if pd.notna(row.get('Party')) else "Unknown"
                
                try:
                    amount = float(row.get('Total Amount INR', 0))
                except:
                    amount = 0
                
                payment = {
                    'id': str(row.name),
                    'type': 'customer',
                    'name': party_value,
                    'total_amount': amount,
                    'pending_amount': amount,
                    'status': formatted_status,
                    'status_color': get_payment_status_color(formatted_status),
                    'reference_type': 'sale',
                    'date': date_value
                }
                pending_payments.append(payment)

        # Apply filters to pending payments
        if type_filter:
            type_filter_lower = type_filter.lower()
            pending_payments = [p for p in pending_payments if p['type'] == type_filter_lower]
        if start_date:
            try:
                start_date = pd.to_datetime(start_date)
                pending_payments = [p for p in pending_payments if p['date'] >= start_date]
            except:
                pass  # Ignore invalid start date
        if end_date:
            try:
                end_date = pd.to_datetime(end_date)
                pending_payments = [p for p in pending_payments if p['date'] <= end_date]
            except:
                pass  # Ignore invalid end date

        return render_template('payments.html', 
                             payments=pending_payments,
                             transactions=transactions,
                             total_pending=total_pending,
                             total_received=total_received,
                             total_purchases=total_purchases,
                             total_sales=total_sales)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        flash(f'Error loading payments: {str(e)}\n{error_details}', 'error')
        return render_template('payments.html', 
                             payments=[],
                             transactions=[],
                             total_pending=0,
                             total_received=0,
                             total_purchases=0,
                             total_sales=0)

@app.route('/add_payment', methods=['POST'])
def add_payment():
    try:
        # Get form data
        payment_type = request.form.get('type')
        name = request.form.get('name')
        amount = float(request.form.get('amount'))
        payment_date = request.form.get('payment_date')
        payment_method = request.form.get('payment_method')
        notes = request.form.get('notes')

        # Load existing payments
        if os.path.exists(PAYMENTS_FILE):
            df = pd.read_excel(PAYMENTS_FILE)
        else:
            df = pd.DataFrame(columns=['id', 'type', 'name', 'total_amount', 'paid_amount', 'pending_amount', 
                                     'status', 'payment_date', 'payment_method', 'notes'])

        # Generate new payment ID
        new_id = str(len(df) + 1)

        # Create new payment record
        new_payment = {
            'id': new_id,
            'type': payment_type,
            'name': name,
            'total_amount': amount,
            'paid_amount': 0,
            'pending_amount': amount,
            'status': 'pending',
            'payment_date': pd.to_datetime(payment_date),
            'payment_method': payment_method,
            'notes': notes
        }

        # Append new payment to DataFrame
        df = pd.concat([df, pd.DataFrame([new_payment])], ignore_index=True)

        # Save to Excel
        df.to_excel(PAYMENTS_FILE, index=False)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/payment_details/<payment_id>')
def payment_details(payment_id):
    try:
        if not os.path.exists(PAYMENTS_FILE):
            flash('No payment records found', 'error')
            return redirect(url_for('payments'))

        df = pd.read_excel(PAYMENTS_FILE)
        payment = df[df['id'] == payment_id].iloc[0].to_dict()

        return render_template('payment_details.html', payment=payment)
    except Exception as e:
        flash(f'Error loading payment details: {str(e)}', 'error')
        return redirect(url_for('payments'))

@app.route('/edit_payment/<payment_id>', methods=['GET', 'POST'])
def edit_payment(payment_id):
    try:
        if not os.path.exists(PAYMENTS_FILE):
            flash('No payment records found', 'error')
            return redirect(url_for('payments'))

        df = pd.read_excel(PAYMENTS_FILE)
        payment = df[df['id'] == payment_id].iloc[0].to_dict()

        if request.method == 'POST':
            # Update payment details
            df.loc[df['id'] == payment_id, 'name'] = request.form.get('name')
            df.loc[df['id'] == payment_id, 'payment_date'] = pd.to_datetime(request.form.get('payment_date'))
            df.loc[df['id'] == payment_id, 'payment_method'] = request.form.get('payment_method')
            df.loc[df['id'] == payment_id, 'notes'] = request.form.get('notes')

            # Update payment status based on amounts
            total_amount = float(df.loc[df['id'] == payment_id, 'total_amount'].iloc[0])
            paid_amount = float(request.form.get('paid_amount', 0))
            pending_amount = total_amount - paid_amount

            df.loc[df['id'] == payment_id, 'paid_amount'] = paid_amount
            df.loc[df['id'] == payment_id, 'pending_amount'] = pending_amount

            if pending_amount <= 0:
                status = 'completed'
            elif paid_amount > 0:
                status = 'partial'
            else:
                status = 'pending'

            df.loc[df['id'] == payment_id, 'status'] = status

            # Save changes
            df.to_excel(PAYMENTS_FILE, index=False)
            flash('Payment updated successfully', 'success')
            return redirect(url_for('payments'))

        return render_template('edit_payment.html', payment=payment)
    except Exception as e:
        flash(f'Error editing payment: {str(e)}', 'error')
        return redirect(url_for('payments'))

def get_inventory_status_color(status):
    """Return Bootstrap color class based on inventory status."""
    status_colors = {
        'in stock': 'success',
        'reserved': 'warning',
        'sold': 'secondary',
        'damaged': 'danger',
        'lost': 'danger'
    }
    return status_colors.get(status.lower(), 'secondary')

@app.route('/inventory')
def inventory():
    try:
        # Load inventory data
        if os.path.exists(INVENTORY_FILE):
            inventory_df = pd.read_excel(INVENTORY_FILE)
        else:
            inventory_df = pd.DataFrame(columns=['id', 'description', 'shape', 'carats', 'color', 'clarity', 'cut', 
                                              'purchase_price', 'market_value', 'status', 'location', 'purchase_date', 'notes'])
            inventory_df.to_excel(INVENTORY_FILE, index=False)
        
        # Apply filters if provided
        shape = request.args.get('shape')
        status = request.args.get('status')
        min_carats = request.args.get('min_carats')
        max_carats = request.args.get('max_carats')
        min_price = request.args.get('min_price')
        max_price = request.args.get('max_price')
        
        filtered_df = inventory_df.copy()
        
        if shape:
            filtered_df = filtered_df[filtered_df['shape'] == shape]
        if status:
            filtered_df = filtered_df[filtered_df['status'] == status]
        if min_carats:
            filtered_df = filtered_df[filtered_df['carats'] >= float(min_carats)]
        if max_carats:
            filtered_df = filtered_df[filtered_df['carats'] <= float(max_carats)]
        if min_price:
            filtered_df = filtered_df[filtered_df['market_value'] >= float(min_price)]
        if max_price:
            filtered_df = filtered_df[filtered_df['market_value'] <= float(max_price)]
        
        # Calculate totals
        total_items = len(filtered_df)
        total_value = filtered_df['market_value'].sum() if not filtered_df.empty else 0
        total_carats = filtered_df['carats'].sum() if not filtered_df.empty else 0
        
        # Count low stock items (items with only 1 in stock)
        low_stock_count = len(filtered_df[filtered_df['status'].str.lower() == 'in stock']) if not filtered_df.empty else 0
        
        # Prepare inventory items for display
        inventory = []
        for _, row in filtered_df.iterrows():
            item = {
                'id': row.get('id', ''),
                'description': row.get('description', ''),
                'shape': row.get('shape', ''),
                'carats': row.get('carats', 0),
                'color': row.get('color', ''),
                'clarity': row.get('clarity', ''),
                'cut': row.get('cut', ''),
                'purchase_price': row.get('purchase_price', 0),
                'market_value': row.get('market_value', 0),
                'status': row.get('status', ''),
                'status_color': get_inventory_status_color(str(row.get('status', ''))),
                'location': row.get('location', ''),
                'notes': row.get('notes', '')
            }
            inventory.append(item)
        
        # Prepare chart data
        shape_counts = filtered_df['shape'].value_counts() if not filtered_df.empty else pd.Series()
        shape_labels = shape_counts.index.tolist()
        shape_data = shape_counts.values.tolist()
        
        clarity_counts = filtered_df['clarity'].value_counts() if not filtered_df.empty else pd.Series()
        clarity_labels = clarity_counts.index.tolist()
        clarity_data = clarity_counts.values.tolist()
        
        return render_template('inventory.html', 
                             inventory=inventory,
                             total_items=total_items,
                             total_value=total_value,
                             total_carats=total_carats,
                             low_stock_count=low_stock_count,
                             shape_labels=shape_labels,
                             shape_data=shape_data,
                             clarity_labels=clarity_labels,
                             clarity_data=clarity_data)
    except Exception as e:
        flash(f'Error loading inventory: {str(e)}', 'error')
        return render_template('inventory.html', 
                             inventory=[],
                             total_items=0,
                             total_value=0,
                             total_carats=0,
                             low_stock_count=0,
                             shape_labels=[],
                             shape_data=[],
                             clarity_labels=[],
                             clarity_data=[])

@app.route('/add_inventory_item', methods=['POST'])
def add_inventory_item():
    try:
        # Get form data
        description = request.form.get('description')
        shape = request.form.get('shape')
        carats = float(request.form.get('carats'))
        color = request.form.get('color')
        clarity = request.form.get('clarity')
        cut = request.form.get('cut')
        purchase_price = float(request.form.get('purchase_price'))
        market_value = float(request.form.get('market_value'))
        status = request.form.get('status')
        location = request.form.get('location')
        notes = request.form.get('notes')
        
        # Load existing inventory
        if os.path.exists(INVENTORY_FILE):
            inventory_df = pd.read_excel(INVENTORY_FILE)
        else:
            inventory_df = pd.DataFrame(columns=['id', 'description', 'shape', 'carats', 'color', 'clarity', 'cut', 
                                              'purchase_price', 'market_value', 'status', 'location', 'purchase_date', 'notes'])
        
        # Generate a unique ID
        item_id = f"D{int(time.time())}"
        
        # Create new item
        new_item = {
            'id': item_id,
            'description': description,
            'shape': shape,
            'carats': carats,
            'color': color,
            'clarity': clarity,
            'cut': cut,
            'purchase_price': purchase_price,
            'market_value': market_value,
            'status': status,
            'location': location,
            'purchase_date': pd.Timestamp.now().strftime('%Y-%m-%d'),
            'notes': notes
        }
        
        # Add to DataFrame
        inventory_df = pd.concat([inventory_df, pd.DataFrame([new_item])], ignore_index=True)
        
        # Save to Excel
        inventory_df.to_excel(INVENTORY_FILE, index=False)
        
        flash('Inventory item added successfully!', 'success')
        return redirect(url_for('inventory'))
    except Exception as e:
        flash(f'Error adding inventory item: {str(e)}', 'error')
        return redirect(url_for('inventory'))

@app.route('/inventory_item_details/<item_id>')
def inventory_item_details(item_id):
    try:
        # Load inventory data
        if not os.path.exists(INVENTORY_FILE):
            flash('Inventory file not found.', 'error')
            return redirect(url_for('inventory'))
        
        inventory_df = pd.read_excel(INVENTORY_FILE)
        
        # Find the item
        item_row = inventory_df[inventory_df['id'] == item_id]
        if item_row.empty:
            flash('Item not found.', 'error')
            return redirect(url_for('inventory'))
        
        # Get item details
        item = item_row.iloc[0].to_dict()
        item['status_color'] = get_inventory_status_color(str(item.get('status', '')))
        
        return render_template('inventory_item_details.html', item=item)
    except Exception as e:
        flash(f'Error loading item details: {str(e)}', 'error')
        return redirect(url_for('inventory'))

@app.route('/edit_inventory_item/<item_id>', methods=['GET', 'POST'])
def edit_inventory_item(item_id):
    try:
        # Load inventory data
        if not os.path.exists(INVENTORY_FILE):
            flash('Inventory file not found.', 'error')
            return redirect(url_for('inventory'))
        
        inventory_df = pd.read_excel(INVENTORY_FILE)
        
        # Find the item
        item_index = inventory_df[inventory_df['id'] == item_id].index
        if len(item_index) == 0:
            flash('Item not found.', 'error')
            return redirect(url_for('inventory'))
        
        if request.method == 'POST':
            # Update item with form data
            inventory_df.at[item_index[0], 'description'] = request.form.get('description')
            inventory_df.at[item_index[0], 'shape'] = request.form.get('shape')
            inventory_df.at[item_index[0], 'carats'] = float(request.form.get('carats'))
            inventory_df.at[item_index[0], 'color'] = request.form.get('color')
            inventory_df.at[item_index[0], 'clarity'] = request.form.get('clarity')
            inventory_df.at[item_index[0], 'cut'] = request.form.get('cut')
            inventory_df.at[item_index[0], 'purchase_price'] = float(request.form.get('purchase_price'))
            inventory_df.at[item_index[0], 'market_value'] = float(request.form.get('market_value'))
            inventory_df.at[item_index[0], 'status'] = request.form.get('status')
            inventory_df.at[item_index[0], 'location'] = request.form.get('location')
            inventory_df.at[item_index[0], 'notes'] = request.form.get('notes')
            
            # Save to Excel
            inventory_df.to_excel(INVENTORY_FILE, index=False)
            
            flash('Inventory item updated successfully!', 'success')
            return redirect(url_for('inventory'))
        else:
            # Get item details for the form
            item = inventory_df.iloc[item_index[0]].to_dict()
            return render_template('edit_inventory_item.html', item=item)
    except Exception as e:
        flash(f'Error editing inventory item: {str(e)}', 'error')
        return redirect(url_for('inventory'))

@app.route('/delete_inventory_item', methods=['POST'])
def delete_inventory_item():
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        
        # Load inventory data
        if os.path.exists(INVENTORY_FILE):
            inventory_df = pd.read_excel(INVENTORY_FILE)
            
            # Find and remove the item
            inventory_df = inventory_df[inventory_df['id'] != item_id]
            
            # Save updated inventory
            inventory_df.to_excel(INVENTORY_FILE, index=False)
            
            return jsonify({'success': True, 'message': 'Item deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Inventory file not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/upload_inventory', methods=['POST'])
def upload_inventory():
    try:
        if 'inventory_file' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('inventory'))
        
        file = request.files['inventory_file']
        
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('inventory'))
        
        if file and file.filename.endswith(('.xlsx', '.xls')):
            # Read the uploaded Excel file
            uploaded_df = pd.read_excel(file)
            
            # Check if the file has the required columns
            required_columns = ['description', 'shape', 'carats', 'color', 'clarity', 'cut', 
                               'purchase_price', 'market_value', 'status']
            
            missing_columns = [col for col in required_columns if col not in uploaded_df.columns]
            
            if missing_columns:
                flash(f'Missing required columns: {", ".join(missing_columns)}', 'error')
                return redirect(url_for('inventory'))
            
            # Load existing inventory
            if os.path.exists(INVENTORY_FILE):
                inventory_df = pd.read_excel(INVENTORY_FILE)
            else:
                inventory_df = pd.DataFrame(columns=['id', 'description', 'shape', 'carats', 'color', 'clarity', 'cut', 
                                                  'purchase_price', 'market_value', 'status', 'location', 'purchase_date', 'notes'])
            
            # Process each row in the uploaded file
            successful_imports = 0
            for _, row in uploaded_df.iterrows():
                try:
                    # Generate a unique ID for each new item
                    item_id = f"D{int(time.time())}{successful_imports}"
                    
                    # Create new item with required fields
                    new_item = {
                        'id': item_id,
                        'description': row.get('description', ''),
                        'shape': row.get('shape', ''),
                        'carats': float(row.get('carats', 0)),
                        'color': row.get('color', ''),
                        'clarity': row.get('clarity', ''),
                        'cut': row.get('cut', ''),
                        'purchase_price': float(row.get('purchase_price', 0)),
                        'market_value': float(row.get('market_value', 0)),
                        'status': row.get('status', 'In Stock'),
                        'location': row.get('location', ''),
                        'purchase_date': pd.Timestamp.now().strftime('%Y-%m-%d'),
                        'notes': row.get('notes', '')
                    }
                    
                    # Add to DataFrame
                    inventory_df = pd.concat([inventory_df, pd.DataFrame([new_item])], ignore_index=True)
                    successful_imports += 1
                    
                    # Add a small delay to ensure unique timestamps for IDs
                    time.sleep(0.01)
                    
                except Exception as e:
                    continue
            
            # Save to Excel
            inventory_df.to_excel(INVENTORY_FILE, index=False)
            
            flash(f'Successfully imported {successful_imports} inventory items!', 'success')
            return redirect(url_for('inventory'))
        else:
            flash('Invalid file format. Please upload an Excel file (.xlsx or .xls)', 'error')
            return redirect(url_for('inventory'))
    except Exception as e:
        flash(f'Error uploading inventory: {str(e)}', 'error')
        return redirect(url_for('inventory'))

@app.route('/download_inventory_template')
def download_inventory_template():
    try:
        # Create a template DataFrame with the required columns
        template_df = pd.DataFrame(columns=['description', 'shape', 'carats', 'color', 'clarity', 'cut', 
                                          'purchase_price', 'market_value', 'status', 'location', 'notes'])
        
        # Add a sample row to help users understand the format
        sample_row = {
            'description': 'Sample Diamond',
            'shape': 'Round',
            'carats': 1.25,
            'color': 'D',
            'clarity': 'VVS1',
            'cut': 'Excellent',
            'purchase_price': 100000,
            'market_value': 120000,
            'status': 'In Stock',
            'location': 'Safe Box 1',
            'notes': 'Sample notes'
        }
        template_df = pd.concat([template_df, pd.DataFrame([sample_row])], ignore_index=True)
        
        # Create a BytesIO object to store the Excel file
        output = io.BytesIO()
        
        # Write the DataFrame to the BytesIO object
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            template_df.to_excel(writer, index=False)
        
        # Seek to the beginning of the BytesIO object
        output.seek(0)
        
        # Return the Excel file as a response
        return send_file(
            output,
            as_attachment=True,
            download_name='inventory_template.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        flash(f'Error generating template: {str(e)}', 'error')
        return redirect(url_for('inventory'))

if __name__ == '__main__':
    app.run(debug=True) 