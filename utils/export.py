"""
Export Functions
Handles CSV and PDF export functionality
"""

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime


def export_to_pdf(report_data, report_name, filters=None):
    """
    Export report data to PDF
    
    Args:
        report_data: Dict with 'dataframe' and optional 'metrics'
        report_name: Name of the report
        filters: Active filters (optional)
        
    Returns:
        bytes: PDF file content
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30
    )
    title = Paragraph(f"NetSuite {report_name}", title_style)
    elements.append(title)
    
    # Date
    date_text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    elements.append(Paragraph(date_text, styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Filters (if provided)
    if filters:
        filter_text = "<b>Active Filters:</b><br/>"
        if filters.get('subsidiaries'):
            filter_text += f"• Subsidiaries: {len(filters['subsidiaries'])} selected<br/>"
        if filters.get('periods'):
            filter_text += f"• Periods: {', '.join(filters['periods'])}<br/>"
        if filters.get('departments'):
            filter_text += f"• Departments: {len(filters['departments'])} selected<br/>"
        if filters.get('account_types'):
            filter_text += f"• Account Types: {', '.join(filters['account_types'])}<br/>"
        
        elements.append(Paragraph(filter_text, styles['Normal']))
        elements.append(Spacer(1, 12))
    
    # Metrics (if provided)
    if 'metrics' in report_data:
        metrics_text = "<b>Summary:</b><br/>"
        for key, value in report_data['metrics'].items():
            metrics_text += f"• {key}: {value}<br/>"
        elements.append(Paragraph(metrics_text, styles['Normal']))
        elements.append(Spacer(1, 12))
    
    # Data table
    df = report_data['dataframe']
    
    # Limit rows for PDF (too many rows can cause issues)
    max_rows = 100
    if len(df) > max_rows:
        df = df.head(max_rows)
        note = Paragraph(
            f"<i>Note: Showing first {max_rows} of {len(report_data['dataframe'])} rows. Download CSV for complete data.</i>",
            styles['Normal']
        )
        elements.append(note)
        elements.append(Spacer(1, 12))
    
    # Convert DataFrame to table data
    table_data = [df.columns.tolist()] + df.values.tolist()
    
    # Create table
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    
    buffer.seek(0)
    return buffer.getvalue()


def create_multi_report_pdf(reports, filters=None):
    """
    Create PDF with multiple reports
    
    Args:
        reports: List of dicts with 'name', 'dataframe', 'metrics'
        filters: Active filters
        
    Returns:
        bytes: PDF file content
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title page
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=1  # Center
    )
    title = Paragraph("NetSuite Financial Reports", title_style)
    elements.append(Spacer(1, 2*inch))
    elements.append(title)
    elements.append(Spacer(1, 0.5*inch))
    
    date_text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    elements.append(Paragraph(date_text, styles['Normal']))
    elements.append(PageBreak())
    
    # Add each report
    for report in reports:
        report_pdf = export_to_pdf(report, report['name'], filters)
        # For simplicity, we'll just add a note that each report is available separately
        elements.append(Paragraph(f"<b>{report['name']}</b>", styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        if 'metrics' in report:
            metrics_text = ""
            for key, value in report['metrics'].items():
                metrics_text += f"• {key}: {value}<br/>"
            elements.append(Paragraph(metrics_text, styles['Normal']))
        
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"See individual PDF export for detailed {report['name']} data.", styles['Italic']))
        elements.append(Spacer(1, 24))
    
    doc.build(elements)
    
    buffer.seek(0)
    return buffer.getvalue()

