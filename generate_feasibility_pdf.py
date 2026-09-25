import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (Pages 2+)
        if self._pageNumber > 1:
            self.drawString(46, 752, "KAMERAPH  |  FEASIBILITY STUDY & STRATEGIC BLUEPRINT")
            self.setFont("Helvetica", 8)
            self.drawRightString(612 - 46, 752, "CONFIDENTIAL")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.6)
            self.line(46, 744, 612 - 46, 744)
            
        # Footer (All Pages)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(46, 32, "KameraPh — AI-Powered High-Volume Portrait & Regalia Platform (Philippines)")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 46, 32, page_text)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.6)
        self.line(46, 42, 612 - 46, 42)
            
        self.restoreState()

def build_feasibility_pdf(filename="KameraPh_Feasibility_Study.pdf"):
    # 612 x 792 points (letter)
    # margins: 46pt left/right, 46pt top/bottom -> usable width = 520pt
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=46,
        rightMargin=46,
        topMargin=46,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()

    # Color Palette
    c_primary = colors.HexColor("#0F172A")    # Deep Slate
    c_secondary = colors.HexColor("#1E3A8A")  # Deep Royal Blue
    c_accent = colors.HexColor("#0284C7")     # Sky Blue / Cyan
    c_dark = colors.HexColor("#1E293B")       # Dark Charcoal
    c_body = colors.HexColor("#334155")       # Body text
    c_light = colors.HexColor("#F8FAFC")      # Light card bg
    c_border = colors.HexColor("#CBD5E1")     # Light border

    # Custom Typography
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=c_primary,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=15,
        textColor=c_secondary,
        spaceAfter=10
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=12.5,
        leading=16,
        textColor=c_secondary,
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=c_body,
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=c_body,
        leftIndent=12,
        spaceAfter=3
    )

    callout_style = ParagraphStyle(
        'DocCallout',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=c_dark
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=10.5,
        textColor=c_body
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.8,
        leading=10.5,
        textColor=c_dark
    )

    story = []

    # =========================================================================
    # PAGE 1: TITLE, METADATA, EXECUTIVE SUMMARY, AND MARKET PROBLEM
    # =========================================================================
    story.append(Paragraph("PROJECT FEASIBILITY & TECHNICAL BLUEPRINT", ParagraphStyle('Badge', fontName='Helvetica-Bold', fontSize=8.5, textColor=c_accent, leading=11, spaceAfter=4)))
    story.append(Paragraph("KameraPh: AI-Powered High-Volume Portrait & Regalia Retouching Platform", title_style))
    story.append(Paragraph("Strategic Feasibility Study: Market Need, Technical Architecture, and Unit Economics for Philippine Studios", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_secondary, spaceBefore=0, spaceAfter=8))

    # Metadata Table (520pt total)
    meta_data = [
        [
            Paragraph("<b>Project:</b> KameraPh Web Platform", table_cell_style),
            Paragraph("<b>Target Audience:</b> PH Studio Photographers, School Contractors", table_cell_style)
        ],
        [
            Paragraph("<b>Primary Niche:</b> High-Volume Graduation Pictorials (Togas & Regalia)", table_cell_style),
            Paragraph("<b>Status:</b> Production Pipeline & Hardened Security v1.0", table_cell_style)
        ],
        [
            Paragraph("<b>Core Stack:</b> FastAPI + React 19 + rembg U2Net + Gemini Vision", table_cell_style),
            Paragraph("<b>Compliance:</b> Philippine Data Privacy Act (RA 10173)", table_cell_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[260, 260])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_light),
        ('BOX', (0,0), (-1,-1), 0.8, c_border),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # 1. Executive Summary
    story.append(Paragraph("1. Executive Summary", h1_style))
    story.append(Paragraph(
        "<b>KameraPh</b> is an AI-powered, browser-based batch retouching and regalia enhancement application designed specifically for the Philippine school portrait and graduation photography industry. While international commercial platforms like Evoto AI, Retouch4me, and Aftershoot exist, they are generic global tools that fail to address the unique operational realities of Philippine studios: they do not offer specialized academic regalia restructuring (togas, sashes, UP sablays, and Barong collars), they frequently over-whiten and alter natural <i>morena</i> skin tones, and their expensive credit-based USD pricing aggressively erodes local studio margins. KameraPh solves these pain points through a localized, cloud-accelerated web platform that automates graduation portrait retouching in seconds at a fraction of the cost.",
        body_style
    ))

    # Executive Callout
    callout_data = [
        [Paragraph(
            "<b>Key Viability Finding:</b> The project demonstrates <b>HIGH OVERALL FEASIBILITY</b>. Leveraging serverless GPU infrastructure (billed by the second) and zero-egress cloud storage allows KameraPh to achieve a raw compute and storage cost of <b>PHP 0.50 to PHP 0.85 per processed photo</b>. Selling at an accessible local market rate of <b>PHP 3.50 to PHP 5.00 per exported high-res photo</b> provides a strong <b>75% to 83% gross profit margin</b> while drastically outperforming manual retouching costs (PHP 15 to PHP 30 per head).",
            callout_style
        )]
    ]
    callout_t = Table(callout_data, colWidths=[520])
    callout_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EFF6FF")),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor("#93C5FD")),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(callout_t)
    story.append(Spacer(1, 8))

    # 2. Market Context & Local Problem Analysis
    story.append(Paragraph("2. Market Context & Philippine Industry Pain Points", h1_style))
    story.append(Paragraph(
        "In the Philippines, graduation pictorials for elementary, junior high, senior high, and universities represent massive commercial contracts where studios photograph 200 to over 2,000 students per school batch. This workflow presents four critical bottlenecks:",
        body_style
    ))
    story.append(Paragraph("• <b>The 'Shared Toga' Dilemma:</b> Because students rotate through the same studio props throughout an 8-hour shooting day, togas become severely creased, hoods and sashes twist off-center, collars become crooked, and safety pins show.", bullet_style))
    story.append(Paragraph("• <b>Tropical Humidity & Lighting Glare:</b> Intense tropical heat combined with continuous studio flash strobes causes oily facial shine, sweat beads, and stray flyaways from electric fans used on set.", bullet_style))
    story.append(Paragraph("• <b>Aesthetic Bias of Existing AI (The Morena Problem):</b> Standard Western and East Asian AI filters routinely lighten and 'whiten' skin, stripping the rich, golden-brown undertones prized by Filipino students and parents.", bullet_style))
    story.append(Paragraph("• <b>Manual Labor Bottleneck & Turnaround Lag:</b> Manual editing in Photoshop takes 3 to 7 minutes per photo. For a 1,000-student school contract, this requires weeks of delay or outsourcing to freelance editors, severely delaying yearbook and print releases.", bullet_style))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: COMPETITIVE ANALYSIS AND TECHNICAL FEASIBILITY
    # =========================================================================
    story.append(Paragraph("3. Competitive Analysis & KameraPh Market Positioning", h1_style))
    story.append(Paragraph(
        "Existing portrait tools provide generalized beauty enhancements but fall short on garment-specific corrections, localization, and pricing models adapted for Philippine photography studios.",
        body_style
    ))

    comp_headers = [
        Paragraph("Platform", table_header_style),
        Paragraph("Core Strength", table_header_style),
        Paragraph("Graduation Studio Fit", table_header_style),
        Paragraph("Pricing & Model", table_header_style),
        Paragraph("KameraPh Advantage", table_header_style)
    ]
    comp_rows = [
        comp_headers,
        [
            Paragraph("<b>Evoto AI</b>", table_cell_bold),
            Paragraph("Portrait skin and clothes wrinkle sliders", table_cell_style),
            Paragraph("High; lacks academic regalia & sablay awareness", table_cell_style),
            Paragraph("Pay-per-export credits (~$0.05 - $0.08 / photo)", table_cell_style),
            Paragraph("Substantially lower PHP pricing; dedicated toga & sash alignment", table_cell_style)
        ],
        [
            Paragraph("<b>Retouch4me</b>", table_cell_bold),
            Paragraph("Fabric and skin AI neural plugins", table_cell_style),
            Paragraph("Moderate; heavy desktop app & complex manual batching", table_cell_style),
            Paragraph("Perpetual license ($120+ per plugin; $600+ full suite)", table_cell_style),
            Paragraph("Zero-install web app; unified one-click graduation pipeline", table_cell_style)
        ],
        [
            Paragraph("<b>Aftershoot</b>", table_cell_bold),
            Paragraph("AI culling & batch Lightroom color grading", table_cell_style),
            Paragraph("Low for garments; great for culling event bursts", table_cell_style),
            Paragraph("Monthly subscription ($20 - $40 / month)", table_cell_style),
            Paragraph("Specialized garment reconstruction & Philippine payment gateways", table_cell_style)
        ],
        [
            Paragraph("<b>Imagen AI</b>", table_cell_bold),
            Paragraph("Personalized Lightroom profile learning", table_cell_style),
            Paragraph("Low for studio graduation; focused on weddings", table_cell_style),
            Paragraph("Pay-per-photo ($0.05+) + monthly commitment", table_cell_style),
            Paragraph("Focus on high-volume studio regalia, skin matte, and backdrop clean", table_cell_style)
        ],
        [
            Paragraph("<b>Photoroom</b>", table_cell_bold),
            Paragraph("Fast background cutout & marketing templates", table_cell_style),
            Paragraph("Basic; suitable only for 2x2 / ID card cutouts", table_cell_style),
            Paragraph("SaaS subscription ($12.99 / month)", table_cell_style),
            Paragraph("High-end portrait skin frequency separation and fabric de-creasing", table_cell_style)
        ]
    ]

    comp_table = Table(comp_rows, colWidths=[65, 115, 115, 110, 115])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_secondary),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_light]),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 8))

    # 4. Technical Feasibility & System Architecture
    story.append(Paragraph("4. Technical Feasibility & Architecture", h1_style))
    story.append(Paragraph(
        "KameraPh utilizes a modern, serverless cloud architecture designed to withstand intermittent Philippine internet connections, eliminate expensive bandwidth penalties, and dynamically scale compute resources on demand.",
        body_style
    ))

    arch_headers = [
        Paragraph("System Layer", table_header_style),
        Paragraph("Recommended Stack", table_header_style),
        Paragraph("Technical Rationale & Operational Advantage", table_header_style)
    ]
    arch_rows = [
        arch_headers,
        [
            Paragraph("<b>Client Web Portal</b>", table_cell_bold),
            Paragraph("React 19, Vite, Tailwind CSS, Lucide Icons", table_cell_style),
            Paragraph("Modular studio interface with interactive comparison slider, batch filmstrip queue, real-time quality diagnostics, and DFA/PRC print cropping modes.", table_cell_style)
        ],
        [
            Paragraph("<b>Backend & API Gateway</b>", table_cell_bold),
            Paragraph("FastAPI (Python 3.11+), Uvicorn", table_cell_style),
            Paragraph("High-performance asynchronous REST API with session tokens, strict CORS whitelist, input payload validation, and non-blocking streaming responses.", table_cell_style)
        ],
        [
            Paragraph("<b>Database & Multi-Tenancy</b>", table_cell_bold),
            Paragraph("PostgreSQL / SQLite with Row-Level Security", table_cell_style),
            Paragraph("Strict multi-tenant tenant isolation policies (RLS). Every studio's batches, photos, and export bundles are completely isolated.", table_cell_style)
        ],
        [
            Paragraph("<b>AI Vision & Matting Engine</b>", table_cell_bold),
            Paragraph("rembg (U2Net) + OpenCV CIELAB + Gemini Vision", table_cell_style),
            Paragraph("Real neural background matting preserving tassels, mortarboards, and hoods. Morena skin tone protection (ΔL* ≤ 3.5) with Gemini multimodal quality analysis.", table_cell_style)
        ],
        [
            Paragraph("<b>Elastic GPU Compute</b>", table_cell_bold),
            Paragraph("Dual Mode: Modal.com GPU / Local CPU", table_cell_style),
            Paragraph("Autoscaling serverless Nvidia A10G/L4 cloud GPU execution for massive cohorts, with local CPU fallback for offline provincial shoot days.", table_cell_style)
        ],
        [
            Paragraph("<b>Payment & Credit Engine</b>", table_cell_bold),
            Paragraph("PayMongo Philippines (HMAC-SHA256)", table_cell_style),
            Paragraph("Automated credit top-ups verified by signed cryptographic webhooks with replay attack prevention, supporting GCash, Maya, and cards.", table_cell_style)
        ]
    ]

    arch_table = Table(arch_rows, colWidths=[95, 140, 285])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_secondary),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_light]),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
    ]))
    story.append(arch_table)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: UNIT ECONOMICS, RISKS, ROADMAP, AND CONCLUSION
    # =========================================================================
    story.append(Paragraph("5. Financial Feasibility & Unit Economics", h1_style))
    story.append(Paragraph(
        "By avoiding dedicated 24/7 GPU server leases and leveraging zero-egress cloud storage, KameraPh operates with exceptionally low per-unit costs, allowing high profitability even at accessible Philippine pricing levels.",
        body_style
    ))

    econ_headers = [
        Paragraph("Cost Component / Metric", table_header_style),
        Paragraph("PHP Value", table_header_style),
        Paragraph("USD Equiv.", table_header_style),
        Paragraph("Operational Assumption / Basis", table_header_style)
    ]
    econ_rows = [
        econ_headers,
        [
            Paragraph("Serverless GPU Inference (Modal.com)", table_cell_style),
            Paragraph("PHP 0.50 - 0.75", table_cell_bold),
            Paragraph("~$0.009 - $0.013", table_cell_style),
            Paragraph("2.5 to 3.5 seconds compute on Nvidia A10G ($0.0003/sec)", table_cell_style)
        ],
        [
            Paragraph("Cloud Storage & Bandwidth (Cloudflare R2)", table_cell_style),
            Paragraph("PHP 0.05", table_cell_bold),
            Paragraph("~$0.0009", table_cell_style),
            Paragraph("Zero egress fee; 15MB file stored for 30-day client delivery", table_cell_style)
        ],
        [
            Paragraph("Database & Web Infrastructure", table_cell_style),
            Paragraph("PHP 0.04", table_cell_bold),
            Paragraph("~$0.0007", table_cell_style),
            Paragraph("Pro-rated across monthly volume of 10,000+ photos", table_cell_style)
        ],
        [
            Paragraph("<b>Total Raw Operational Cost per Photo</b>", table_cell_bold),
            Paragraph("<b>PHP 0.59 - 0.84</b>", table_cell_bold),
            Paragraph("<b>~$0.011 - $0.015</b>", table_cell_bold),
            Paragraph("Full direct cost per processed high-res image", table_cell_style)
        ],
        [
            Paragraph("<b>Retail Price to Studio (Per Photo)</b>", table_cell_bold),
            Paragraph("<b>PHP 3.50 - 5.00</b>", table_cell_bold),
            Paragraph("<b>~$0.062 - $0.089</b>", table_cell_bold),
            Paragraph("Massive savings vs. manual hiring (PHP 15 - 30 / student)", table_cell_style)
        ],
        [
            Paragraph("<b>Projected Gross Profit Margin</b>", table_cell_bold),
            Paragraph("<b>76.0% - 83.2%</b>", table_cell_bold),
            Paragraph("<b>High Margin</b>", table_cell_bold),
            Paragraph("Provides robust buffer for marketing, QA, and local support", table_cell_style)
        ]
    ]

    econ_table = Table(econ_rows, colWidths=[150, 95, 85, 190])
    econ_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_secondary),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_light]),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
    ]))
    story.append(econ_table)
    story.append(Spacer(1, 8))

    # 6. Risk Assessment & Strategic Mitigation
    story.append(Paragraph("6. Key Risks & Mitigation Strategy", h1_style))
    story.append(Paragraph("• <b>Internet Instability in Provincial Locations:</b> Philippine provincial schools often lack high-speed fiber. <i>Mitigation:</i> KameraPh enforces client-side thumbnail downsampling for real-time preview, while full-resolution raw processing uses resumable chunked background uploads (Tus protocol).", bullet_style))
    story.append(Paragraph("• <b>Cultural & Institutional Regalia Variation:</b> Academic hoods, medals, school logos, and UP Sablays have unique geometric weaves. <i>Mitigation:</i> KameraPh builds an emblem-masking layer ensuring AI fabric smoothing only affects plain cloth while leaving insignia, embroidery, and honors cords crisp.", bullet_style))
    story.append(Paragraph("• <b>Graduation Seasonality (Peak vs. Off-Peak):</b> Revenue may concentrate heavily between March and July. <i>Mitigation:</i> Secondary presets for year-round revenue drivers, including PRC board exam IDs, corporate headshots, and debutante pictorials.", bullet_style))
    story.append(Spacer(1, 8))

    # 7. Phased Implementation Roadmap
    story.append(Paragraph("7. Implementation Roadmap & Timeline", h1_style))
    roadmap_headers = [Paragraph("Phase", table_header_style), Paragraph("Duration", table_header_style), Paragraph("Milestones & Core Deliverables", table_header_style)]
    roadmap_rows = [
        roadmap_headers,
        [
            Paragraph("<b>Phase 1: Proof of Concept</b>", table_cell_bold),
            Paragraph("Weeks 1 - 3", table_cell_style),
            Paragraph("Develop core Python vision pipeline on Modal; test toga segmentation, fabric de-crease, and morena-preserving skin retouching on 100 sample student photos.", table_cell_style)
        ],
        [
            Paragraph("<b>Phase 2: MVP Web Platform</b>", table_cell_bold),
            Paragraph("Weeks 4 - 7", table_cell_style),
            Paragraph("Build Next.js web application, Cloudflare R2 direct upload pipeline, batch job dashboard, and interactive before/after inspection slider.", table_cell_style)
        ],
        [
            Paragraph("<b>Phase 3: Studio Beta & Launch</b>", table_cell_bold),
            Paragraph("Weeks 8 - 10", table_cell_style),
            Paragraph("Integrate PayMongo (GCash / Maya) checkout, conduct private pilot testing with 5 to 10 partner Philippine studios during live school shoots, and release v1.0.", table_cell_style)
        ]
    ]

    roadmap_table = Table(roadmap_rows, colWidths=[110, 75, 335])
    roadmap_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_secondary),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_light]),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
    ]))
    story.append(roadmap_table)
    story.append(Spacer(1, 8))

    # 8. Conclusion
    story.append(Paragraph("8. Strategic Recommendation & Next Steps", h1_style))
    story.append(Paragraph(
        "<b>VERDICT: HIGH FEASIBILITY — PROCEED TO DEVELOPMENT.</b> KameraPh possesses a clear market wedge in the Philippine photography sector. It addresses acute, daily labor bottlenecks that existing global software ignores, supported by an ultra-lean serverless cost architecture yielding 75%+ gross margins. The recommended immediate next step is the construction of the Phase 1 Proof-of-Concept AI pipeline to validate regalia smoothing fidelity.",
        body_style
    ))

    # Build the PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated: {filename}")

if __name__ == "__main__":
    build_feasibility_pdf()
