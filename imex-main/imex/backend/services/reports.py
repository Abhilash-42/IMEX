import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
from typing import Dict, List
import io
import logging

logger = logging.getLogger(__name__)

class PDFReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom styles for reports"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#FF6B00'),
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#333333'),
            spaceAfter=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomSectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#FF6B00'),
            spaceAfter=8
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomBodyText',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomRiskHigh',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#DC2626'),
            fontWeight='bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomRiskMedium',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#F59E0B'),
            fontWeight='bold'
        ))
    
    def generate_risk_report(self, risk_data: Dict) -> bytes:
        """Generate PDF risk report"""
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        
        # Title
        story.append(Paragraph("chainSol AI - Risk Assessment Report", self.styles['Title']))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                              self.styles['BodyText']))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        story.append(Paragraph(risk_data.get('executive_summary', ''), self.styles['BodyText']))
        story.append(Spacer(1, 15))
        
        # Key Metrics
        story.append(Paragraph("Key Metrics", self.styles['SectionHeader']))
        
        risk_score = risk_data.get('risk_score', 0)
        risk_style = 'RiskHigh' if risk_score > 70 else 'RiskMedium' if risk_score > 50 else 'BodyText'
        
        metrics_data = [
            ["Risk Score", f"{risk_score:.0f}/100"],
            ["Revenue Exposure", f"${risk_data.get('revenue_exposure', 0):,.0f}M"],
            ["Affected Suppliers", str(len(risk_data.get('affected_suppliers', [])))],
            ["Affected Products", str(len(risk_data.get('affected_products', [])))],
            ["Event Severity", f"{risk_data.get('event_severity', 0):.0f}/100"]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2*inch, 2*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#FEE2E2') if risk_score > 70 else colors.white),
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 15))
        
        # Affected Suppliers
        story.append(Paragraph("Affected Suppliers", self.styles['SectionHeader']))
        
        suppliers = risk_data.get('affected_suppliers', [])
        if suppliers:
            supplier_data = [["Supplier", "Criticality", "Status"]]
            for s in suppliers[:10]:  # Limit to 10
                supplier_data.append([
                    s.get('name', 'Unknown'),
                    f"{s.get('criticality', 0):.0f}/100",
                    "Critical" if s.get('criticality', 0) > 70 else "High" if s.get('criticality', 0) > 50 else "Medium"
                ])
            
            supplier_table = Table(supplier_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
            supplier_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            story.append(supplier_table)
        else:
            story.append(Paragraph("No affected suppliers identified.", self.styles['BodyText']))
        
        story.append(Spacer(1, 15))
        
        # Recommendations
        story.append(Paragraph("Recommendations", self.styles['SectionHeader']))
        
        recommendations = risk_data.get('recommendations', [])
        if recommendations:
            list_items = []
            for rec in recommendations:
                list_items.append(ListItem(Paragraph(rec, self.styles['BodyText'])))
            
            story.append(ListFlowable(list_items, bulletType='bullet', start='bullet'))
        else:
            story.append(Paragraph("No recommendations generated.", self.styles['BodyText']))
        
        story.append(Spacer(1, 15))
        
        # Footer
        story.append(Paragraph("Confidential - For internal use only", 
                              ParagraphStyle(
                                  name='Footer',
                                  parent=self.styles['Normal'],
                                  fontSize=8,
                                  textColor=colors.grey,
                                  alignment=TA_CENTER
                              )))
        
        # Build PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes

# Singleton instance
pdf_generator = PDFReportGenerator()
