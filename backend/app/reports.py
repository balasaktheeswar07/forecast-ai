import os
import io
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from botocore.exceptions import ClientError
from .aws_client import (
    get_s3_client,
    REPORTS_BUCKET,
    check_aws_connection
)

logger = logging.getLogger("forecast-ai-reports")

def generate_pdf_report(forecast_summary: dict, insights_text: str) -> io.BytesIO:
    """
    Generates a beautifully styled marketing forecast report PDF.
    Returns a BytesIO stream containing the PDF binary.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom color palette matching the application
    primary_color = colors.HexColor("#0f172a") # Deep Slate
    secondary_color = colors.HexColor("#3b82f6") # Blue
    accent_color = colors.HexColor("#10b981") # Green
    text_color = colors.HexColor("#334155") # Muted dark text
    light_bg = colors.HexColor("#f8fafc") # Very light grey
    
    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        "DocSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=20
    )
    
    h1_style = ParagraphStyle(
        "DocH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=primary_color,
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        "DocH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=secondary_color,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=text_color,
        spaceAfter=8
    )
    
    bold_body_style = ParagraphStyle(
        "DocBodyBold",
        parent=body_style,
        fontName="Helvetica-Bold"
    )
    
    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=text_color
    )

    story = []
    
    # 1. Header Banner
    story.append(Paragraph("AI FORECASTING ASSISTANT", title_style))
    date_str = datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph(f"Digital Marketing Performance Forecast & Budget Optimization • {date_str}", subtitle_style))
    story.append(Spacer(1, 10))
    
    # 2. Key Metrics Callout Table
    hist_rev = forecast_summary.get("historical_revenue", 0.0)
    proj_rev = forecast_summary.get("projected_revenue", 0.0)
    hist_roas = forecast_summary.get("historical_roas", 0.0)
    proj_roas = forecast_summary.get("projected_roas", 0.0)
    
    kpi_data = [
        [
            Paragraph("<b>Historical Revenue (30d)</b>", table_cell_style),
            Paragraph("<b>Projected Revenue (30d)</b>", table_cell_style),
            Paragraph("<b>Historical ROAS</b>", table_cell_style),
            Paragraph("<b>Projected ROAS</b>", table_cell_style)
        ],
        [
            Paragraph(f"${hist_rev:,.2f}", bold_body_style),
            Paragraph(f"${proj_rev:,.2f}", bold_body_style),
            Paragraph(f"{hist_roas:.2f}x", bold_body_style),
            Paragraph(f"{proj_roas:.2f}x", bold_body_style)
        ]
    ]
    
    kpi_table = Table(kpi_data, colWidths=[1.8*inch, 1.8*inch, 1.4*inch, 1.4*inch])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TEXTCOLOR', (0,0), (-1,-1), text_color),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.HexColor("#e2e8f0")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 20))
    
    # 3. Channel Breakdown Table
    story.append(Paragraph("Channel Performance Forecast", h1_style))
    
    table_data = [[
        Paragraph("Channel", table_header_style),
        Paragraph("Spend", table_header_style),
        Paragraph("Impressions", table_header_style),
        Paragraph("Clicks", table_header_style),
        Paragraph("Conversions", table_header_style),
        Paragraph("Revenue", table_header_style),
        Paragraph("ROAS", table_header_style)
    ]]
    
    channels = forecast_summary.get("channels", {})
    for ch_name, ch_metrics in channels.items():
        table_data.append([
            Paragraph(ch_name, table_cell_style),
            Paragraph(f"${ch_metrics.get('spend', 0):,.2f}", table_cell_style),
            Paragraph(f"{ch_metrics.get('impressions', 0):,.0f}", table_cell_style),
            Paragraph(f"{ch_metrics.get('clicks', 0):,.0f}", table_cell_style),
            Paragraph(f"{ch_metrics.get('conversions', 0):,.1f}", table_cell_style),
            Paragraph(f"${ch_metrics.get('revenue', 0):,.2f}", table_cell_style),
            Paragraph(f"{ch_metrics.get('roas', 0):.2f}x", table_cell_style)
        ])
        
    ch_table = Table(table_data, colWidths=[1.2*inch, 1.0*inch, 1.0*inch, 0.8*inch, 0.9*inch, 1.1*inch, 0.8*inch])
    ch_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_bg]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    story.append(ch_table)
    story.append(Spacer(1, 20))
    
    # 4. AI Strategic Recommendations Section
    story.append(Paragraph("AI Strategic Recommendations", h1_style))
    
    # Simple markdown parser for headers/bullets in insights_text
    lines = insights_text.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Parse Headers
        if line.startswith("## "):
            header_text = line.replace("## ", "").strip()
            story.append(Paragraph(header_text, h1_style))
        elif line.startswith("### "):
            header_text = line.replace("### ", "").strip()
            story.append(Paragraph(header_text, h2_style))
        elif line.startswith("- ") or line.startswith("* "):
            bullet_text = line[2:].strip()
            # Basic bold parsing **text** -> <b>text</b>
            bullet_text = bullet_text.replace("**", "<b>", 1).replace("**", "</b>", 1)
            story.append(Paragraph(f"• {bullet_text}", body_style))
        else:
            line = line.replace("**", "<b>", 1).replace("**", "</b>", 1)
            story.append(Paragraph(line, body_style))
            
    # Build Document
    doc.build(story)
    buffer.seek(0)
    return buffer

def save_report_and_get_url(pdf_buffer: io.BytesIO, filename: str) -> str:
    """
    Saves PDF report to S3 (returns Presigned URL) or local storage (returns download path).
    """
    pdf_bytes = pdf_buffer.getvalue()
    
    if check_aws_connection():
        s3 = get_s3_client()
        try:
            s3.put_object(
                Bucket=REPORTS_BUCKET,
                Key=filename,
                Body=pdf_bytes,
                ContentType="application/pdf"
            )
            # Generate pre-signed URL valid for 1 hour (3600 seconds)
            url = s3.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": REPORTS_BUCKET, "Key": filename},
                ExpiresIn=3600
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to upload report to S3: {e}. Falling back to local.")
            
    # Fallback to local storage
    os.makedirs("data/reports", exist_ok=True)
    local_path = os.path.join("data", "reports", filename)
    with open(local_path, "wb") as f:
        f.write(pdf_bytes)
        
    # Return local relative static route path
    return f"/api/download-report/{filename}"
