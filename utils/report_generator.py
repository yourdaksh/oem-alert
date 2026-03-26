
from fpdf import FPDF
from datetime import datetime
import os
import tempfile
from typing import List, Any

class PDFReport(FPDF):
    def header(self):
        # Logo could be added here if available
        # self.image('logo.png', 10, 8, 33)
        self.set_font('Arial', 'B', 15)
        self.cell(80)
        self.cell(30, 10, 'Executive Vulnerability Briefing', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}} - Generated on {datetime.now().strftime("%Y-%m-%d")}', 0, 0, 'C')

def generate_pdf_report(vulnerabilities: List[Any]) -> bytes:
    """
    Generate a PDF report for the given list of vulnerabilities.
    Returns the PDF content as bytes.
    """
    pdf = PDFReport()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)
    
    # Title Section
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f'Weekly Security Overview - {datetime.now().strftime("%B %d, %Y")}', 0, 1)
    pdf.ln(5)
    
    # Summary Metrics
    pdf.set_font('Arial', 'B', 12)
    total = len(vulnerabilities)
    critical = sum(1 for v in vulnerabilities if v.severity_level == 'Critical')
    high = sum(1 for v in vulnerabilities if v.severity_level == 'High')
    open_vulns = sum(1 for v in vulnerabilities if getattr(v, 'status', 'Open') == 'Open')
    
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, f"Total Vulnerabilities: {total} | Critical: {critical} | High: {high} | Open: {open_vulns}", 1, 1, 'L', fill=True)
    pdf.ln(10)
    
    # Table Header
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(30, 10, 'Severity', 1, 0, 'C', fill=True)
    pdf.cell(40, 10, 'OEM', 1, 0, 'C', fill=True)
    pdf.cell(80, 10, 'Product', 1, 0, 'C', fill=True)
    pdf.cell(40, 10, 'Status', 1, 1, 'C', fill=True)
    
    # Table Content
    pdf.set_font('Arial', '', 9)
    for vuln in vulnerabilities:
        # Severity Color (Pseudo-formatting as FPDF is limited without HTMLMixin)
        severity = vuln.severity_level
        
        pdf.cell(30, 10, severity, 1)
        pdf.cell(40, 10, vuln.oem_name[:20], 1)
        pdf.cell(80, 10, vuln.product_name[:40] + ('...' if len(vuln.product_name) > 40 else ''), 1)
        pdf.cell(40, 10, getattr(vuln, 'status', 'Open'), 1, 1)
        
    # Return bytes
    return pdf.output(dest='S').encode('latin-1')
