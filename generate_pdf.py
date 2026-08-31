import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

PDF_OUTPUT_PATH = "/Users/bhargav/Downloads/copart project/Copart_Conversational_Search_Documentation.pdf"

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(50, letter[1] - 30, "Copart Conversational Hybrid Search — Architecture & Testing Guide")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(50, letter[1] - 34, letter[0] - 50, letter[1] - 34)
            
        # Footer
        self.setFont("Helvetica", 8)
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 50, 28, footer_text)
        self.drawString(50, 28, "Copart Take-Home Project: Hybrid SQL + Semantic RAG Implementation")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(50, 38, letter[0] - 50, 38)
        self.restoreState()

def build_pdf():
    doc = SimpleDocTemplate(
        PDF_OUTPUT_PATH,
        pagesize=letter,
        leftMargin=50,
        rightMargin=50,
        topMargin=42,
        bottomMargin=42
    )

    styles = getSampleStyleSheet()
    content_width = letter[0] - 100
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=19,
        leading=22,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=2
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#475569"),
        spaceAfter=8
    )
    
    h1_style = ParagraphStyle(
        'Header1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12.5,
        leading=15.5,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'Header2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#2563eb"),
        spaceBefore=5,
        spaceAfter=2,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.6,
        leading=11.8,
        textColor=colors.HexColor("#334155"),
        spaceAfter=2.5
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.6,
        leading=11.8,
        textColor=colors.HexColor("#334155"),
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=2
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.4,
        leading=11.4,
        textColor=colors.HexColor("#1e293b")
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.8,
        leading=10,
        textColor=colors.HexColor("#0f172a")
    )

    story = []

    # ==================== PAGE 1: OVERVIEW & HYBRID ARCHITECTURE ====================
    story.append(Paragraph("Copart Conversational Hybrid Search System", title_style))
    story.append(Paragraph("Structured SQL + Semantic Inspector Notes RAG & Knowledge Base Documentation", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceAfter=6))

    summary_data = [[
        Paragraph(
            "<b>Executive Summary:</b> Implements an enterprise-grade <b>Hybrid Conversational Search</b> platform for Copart vehicle buyers. "
            "It marries <b>Deterministic SQL Filters</b> (for exact bounds: price, make, year, location) with <b>Semantic Vector/FTS5 RAG</b> "
            "(for unstructured mechanic inspection notes like <i>'airbags intact'</i>, <i>'easy DIY fix'</i>, <i>'light hail for PDR'</i>) and "
            "an integrated <b>Copart Policy Knowledge Base</b> (explaining salvage titles, broker bidding, and condition codes).<br/>"
            "<b>Stack:</b> React + Vite (Frontend) &bull; FastAPI Python (Backend) &bull; SQLite + FTS5 BM25 (Hybrid Database) &bull; Gemini 3.6 Flash / OpenAI Tool Calling.",
            callout_style
        )
    ]]
    summary_table = Table(summary_data, colWidths=[content_width])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f0f7ff")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#93c5fd")),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 4))

    story.append(Paragraph("1. How Hybrid Search Works (Real-World Analogy)", h1_style))
    story.append(Paragraph(
        "Standard search engines make you choose between rigid dropdowns or loose keyword search. Our Hybrid Search gives buyers both simultaneously:",
        body_style
    ))
    story.append(Paragraph("&bull; <b>Structured Query:</b> <i>'Toyota SUVs in Texas under $15k'</i> &rarr; Database uses B-Tree indexes to strictly filter matching cars in &lt;2ms.", bullet_style))
    story.append(Paragraph("&bull; <b>Semantic / Inspector RAG:</b> <i>'Easy to fix with no airbag damage'</i> &rarr; RAG searches unstructured mechanic notes to find low-severity collision lots.", bullet_style))
    story.append(Paragraph("&bull; <b>Copart Policy RAG:</b> <i>'What does Enhanced Vehicle mean?'</i> &rarr; Retrieves official Copart definitions and guidance inside the chat.", bullet_style))
    story.append(Paragraph("&bull; <b>Multi-Turn Memory:</b> <i>'Actually make it Honda'</i> &rarr; Swaps Make to Honda while keeping price, state, and inspection criteria intact.", bullet_style))
    story.append(Spacer(1, 3))

    story.append(Paragraph("2. End-to-End Hybrid Search Workflow", h1_style))
    flow_table_data = [
        [Paragraph("<b>Step</b>", body_style), Paragraph("<b>Layer</b>", body_style), Paragraph("<b>What Happens Behind the Scenes</b>", body_style)],
        [
            Paragraph("<b>1</b>", body_style),
            Paragraph("<b>React UI</b><br/>(Port 5173)", body_style),
            Paragraph("User enters query (e.g. <i>'Toyota SUVs easy to fix with no airbag damage'</i>). Dispatches <code>POST /chat</code> payload.", body_style)
        ],
        [
            Paragraph("<b>2</b>", body_style),
            Paragraph("<b>FastAPI Gateway</b><br/>(Port 8000)", body_style),
            Paragraph("<code>main.py</code> pulls session state, loads history from <code>session.py</code>, and injects Copart domain instructions.", body_style)
        ],
        [
            Paragraph("<b>3</b>", body_style),
            Paragraph("<b>LLM Agent & RAG</b><br/>(<code>agent.py</code>)", body_style),
            Paragraph("Extracts structured params (<code>make: Toyota</code>) AND semantic query (<code>semantic_query: 'easy fix DIY airbags intact'</code>). Queries policy knowledge base.", body_style)
        ],
        [
            Paragraph("<b>4</b>", body_style),
            Paragraph("<b>Session State</b><br/>(<code>session.py</code>)", body_style),
            Paragraph("Merges newly extracted parameters into active session filters (preserving prior turn filters unless overridden).", body_style)
        ],
        [
            Paragraph("<b>5</b>", body_style),
            Paragraph("<b>Hybrid DB Engine</b><br/>(<code>inventory.py</code>)", body_style),
            Paragraph("Runs combined SQL query: hard SQL <code>WHERE</code> clauses for price/make/state + FTS5 BM25 ranking on <code>inspector_notes</code>.", body_style)
        ],
        [
            Paragraph("<b>6</b>", body_style),
            Paragraph("<b>Live UI Update</b>", body_style),
            Paragraph("React renders conversational response, Copart policy guide tips, active filter tags, and vehicle cards with technician note excerpts.", body_style)
        ]
    ]

    t = Table(flow_table_data, colWidths=[26, 105, content_width - 131])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 3.5),
    ]))
    story.append(t)

    # ==================== PAGE 2: BACKEND DEEP DIVE ====================
    story.append(PageBreak())
    story.append(Paragraph("3. Deep Dive: Backend Codebase & Architecture", h1_style))
    story.append(Paragraph("All backend source code lives inside <code>backend/</code>. Below is the exact technical function of every module:", body_style))
    story.append(Spacer(1, 3))

    story.append(Paragraph("A. main.py — The API Gateway & Traffic Controller", h2_style))
    story.append(Paragraph(
        "<b>Role:</b> Central FastAPI router coordinating the conversational AI pipeline.<br/>"
        "&bull; <code>POST /chat</code>: Receives user message, runs agent, merges session state, queries hybrid DB, and returns dialogue + vehicles + policy guidance.<br/>"
        "&bull; <code>GET /vehicles</code>: Direct programmatic vehicle search with filter and semantic query parameters (e.g. <code>?make=Toyota&semantic_query=hail</code>).<br/>"
        "&bull; <code>GET /filter-options</code> & <code>GET /health</code>: Dynamic UI filter bounds and backend liveness verification.",
        body_style
    ))

    story.append(Paragraph("B. agent.py — Hybrid Tool-Calling & Knowledge RAG", h2_style))
    story.append(Paragraph(
        "<b>Role:</b> Translates human language into structured filters, semantic inspector queries, and policy answers.<br/>"
        "&bull; <b>Hybrid Tool Schema:</b> Formal <code>search_vehicles</code> schema accepting <code>make</code>, <code>price_max</code>, <code>location_state</code>, and <code>semantic_query</code>.<br/>"
        "&bull; <b>Multi-Model Flexibility:</b> Connects to Gemini 3.6 Flash (via Google Generative Language API) or OpenAI (via <code>openai</code>).<br/>"
        "&bull; <b>Zero-Cost Fallback Engine:</b> Includes a built-in NLP pattern extractor + SQLite FTS5 RAG matcher for 100% testability without API keys.",
        body_style
    ))

    story.append(Paragraph("C. inventory.py — Hybrid SQL + BM25 Semantic Query Layer", h2_style))
    story.append(Paragraph(
        "<b>Role:</b> Executes safe, high-performance database lookups.<br/>"
        "&bull; <b>Hybrid Ranking:</b> Applies strict SQL filters (<code>price <= 15000</code>) while ranking results by BM25 semantic match score on <code>inspector_notes</code>.<br/>"
        "&bull; <b>Policy Knowledge RAG (<code>query_knowledge_base</code>):</b> Performs instant retrieval on Copart FAQs, title regulations, and auction rules.<br/>"
        "&bull; <b>SQL Injection Safe:</b> Always uses parameterized SQL placeholders (<code>?</code>).",
        body_style
    ))

    story.append(Paragraph("D. session.py — Multi-Turn Memory & State Machine", h2_style))
    story.append(Paragraph(
        "<b>Role:</b> Manages multi-turn conversation memory and filter persistence.<br/>"
        "&bull; <b>Filter Accumulation:</b> Accumulates constraints across turns (e.g. Turn 1: <i>Toyota</i> + Turn 2: <i>under $15k</i> &rarr; <i>[Toyota, &lt;$15k]</i>).<br/>"
        "&bull; <b>Filter Overriding:</b> Replaces values on demand (e.g. <i>'actually show Honda'</i> replaces <code>make</code> while preserving other filters).<br/>"
        "&bull; <b>Sliding History Window:</b> Truncates message history to the last 20 turns to conserve LLM token budget.",
        body_style
    ))

    story.append(Paragraph("E. seed_data.py & models.py — Data Generation & Validation", h2_style))
    story.append(Paragraph(
        "&bull; <b>seed_data.py:</b> Generates 500 realistic vehicles with authentic VINs, lot numbers, and detailed mechanic inspector notes.<br/>"
        "&bull; <b>models.py:</b> Pydantic schemas (<code>Vehicle</code>, <code>VehicleFilters</code>, <code>ChatRequest</code>, <code>ChatResponse</code>) ensuring strict type safety.",
        body_style
    ))

    # ==================== PAGE 3: FRONTEND DEEP DIVE & AI TRAP ====================
    story.append(PageBreak())
    story.append(Paragraph("4. Deep Dive: Frontend Components & UI System", h1_style))
    story.append(Paragraph("All frontend code resides in <code>frontend/src/</code>, built with React 18, Vite, and custom CSS:", body_style))
    story.append(Spacer(1, 3))

    frontend_table_data = [
        [Paragraph("<b>Component / File</b>", body_style), Paragraph("<b>Visual & Functional Role</b>", body_style)],
        [
            Paragraph("<b>App.jsx</b>", body_style),
            Paragraph("Root layout coordinator. Manages global state (vehicle result list, active filter object, total matches) and seamlessly links the left Chat Panel with the right Results Grid.", body_style)
        ],
        [
            Paragraph("<b>ChatInterface.jsx</b>", body_style),
            Paragraph("Interactive dialogue sidebar with hybrid search suggestion chips (e.g. <i>'Toyota SUVs easy to fix with no airbag damage'</i>), auto-expanding textarea, typing animations, and reset button.", body_style)
        ],
        [
            Paragraph("<b>VehicleCard.jsx</b>", body_style),
            Paragraph("Vehicle card displaying vehicle photo, price, year/make/model, lot number, location, mileage, transmission, damage type, color-coded condition badge, and a dedicated <b>Inspector Note Excerpt</b>.", body_style)
        ],
        [
            Paragraph("<b>FilterPanel.jsx</b>", body_style),
            Paragraph("Active filters bar displaying extracted structured filters (e.g. <code>[Make: Toyota]</code>) and semantic search tags (e.g. <code>[Inspector Search: easy fix DIY]</code>).", body_style)
        ],
        [
            Paragraph("<b>ConversationBubble.jsx</b>", body_style),
            Paragraph("Renders user message bubbles (blue gradient, right aligned) and assistant bubbles (dark slate, left aligned) with timestamps and animated typing dots.", body_style)
        ],
        [
            Paragraph("<b>index.css</b>", body_style),
            Paragraph("Comprehensive dark-mode design system with glassmorphism cards, smooth hover micro-animations, glowing focus borders, inspector note boxes, and responsive layouts.", body_style)
        ],
        [
            Paragraph("<b>vite.config.js</b>", body_style),
            Paragraph("Configures lightning-fast local development with Hot Module Replacement (HMR) and an automatic proxy routing <code>/chat</code> and <code>/vehicles</code> requests directly to FastAPI on port 8000.", body_style)
        ]
    ]

    ft = Table(frontend_table_data, colWidths=[115, content_width - 115])
    ft.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(ft)
    story.append(Spacer(1, 6))

    story.append(Paragraph("5. Security, Guardrails & Reliability Architecture", h1_style))
    security_data = [[
        Paragraph(
            "<b>Engineering & Reliability Principles:</b><br/>"
            "&bull; <b>SQL Injection Prevention:</b> All database queries compile strictly via parameterized placeholders (<code>?</code>), preventing arbitrary SQL execution regardless of user query contents.<br/>"
            "&bull; <b>Strict Type Safety:</b> Pydantic v2 data models enforce validation on all inbound chat payloads, search filters, and outgoing vehicle records.<br/>"
            "&bull; <b>Provider Resilience & Graceful Degradation:</b> Pluggable LLM architecture routes seamlessly between Gemini and OpenAI, with automatic fallback to local rule-based parsing if network or quota issues occur.<br/>"
            "&bull; <b>Bounded Memory:</b> Multi-turn conversation sessions maintain an active sliding window to prevent unbounded memory growth and optimize context consumption.",
            callout_style
        )
    ]]
    security_table = Table(security_data, colWidths=[content_width])
    security_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#86efac")),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(security_table)

    # ==================== PAGE 4: TESTING & ROADMAP ====================
    story.append(PageBreak())
    story.append(Paragraph("6. Step-by-Step Testing & Verification Commands", h1_style))
    story.append(Paragraph("Run the commands below in your terminal to launch and test the entire stack:", body_style))
    story.append(Spacer(1, 3))

    story.append(Paragraph("Step 1: Start Backend API (Terminal 1)", h2_style))
    cmd_1 = """cd "/Users/bhargav/Downloads/copart project/backend"
source venv/bin/activate
uvicorn main:app --reload --port 8000"""
    t_cmd1 = Table([[Paragraph(f"<font face='Courier'>{cmd_1.replace(chr(10), '<br/>')}</font>", code_style)]], colWidths=[content_width])
    t_cmd1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 4.5)
    ]))
    story.append(t_cmd1)
    story.append(Spacer(1, 3))

    story.append(Paragraph("Step 2: Start Frontend Application (Terminal 2)", h2_style))
    cmd_2 = """cd "/Users/bhargav/Downloads/copart project/frontend"
npm run dev"""
    t_cmd2 = Table([[Paragraph(f"<font face='Courier'>{cmd_2.replace(chr(10), '<br/>')}</font>", code_style)]], colWidths=[content_width])
    t_cmd2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 4.5)
    ]))
    story.append(t_cmd2)
    story.append(Paragraph("<i>Open <b>http://localhost:5173</b> in your browser to interact with the UI.</i>", body_style))
    story.append(Spacer(1, 3))

    story.append(Paragraph("Step 3: Test Hybrid Search & Policy RAG via cURL (Terminal 3)", h2_style))
    cmd_3 = """# 1. Health check
curl http://localhost:8000/health

# 2. Hybrid Search Test: Structured SQL + Semantic Inspector Notes
curl -s -X POST http://localhost:8000/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Show me Toyota SUVs easy to fix with no airbag damage"}' | python3 -m json.tool

# 3. Policy Knowledge RAG Test: Copart Guidelines
curl -s -X POST http://localhost:8000/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message": "What does Enhanced Vehicle mean at Copart?"}' | python3 -m json.tool

# 4. Multi-Turn Search Refinement Test
SESSION=$(curl -s -X POST http://localhost:8000/chat -H "Content-Type: application/json" \\
  -d '{"message": "Show me Ford trucks"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")

curl -s -X POST http://localhost:8000/chat -H "Content-Type: application/json" \\
  -d "{\\"message\\": \\"Under $15000\\", \\"session_id\\": \\"$SESSION\\"}" | python3 -m json.tool"""

    t_cmd3 = Table([[Paragraph(f"<font face='Courier'>{cmd_3.replace(chr(10), '<br/>')}</font>", code_style)]], colWidths=[content_width])
    t_cmd3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 4.5)
    ]))
    story.append(t_cmd3)
    story.append(Spacer(1, 5))

    story.append(Paragraph("7. Evolution to Production & Enterprise Scaling", h1_style))
    story.append(Paragraph("&bull; <b>Database & Scale:</b> Migrate SQLite to PostgreSQL with <code>pgvector</code> or OpenSearch for hybrid semantic (embedding) and faceted search across millions of salvage inventory lots.", bullet_style))
    story.append(Paragraph("&bull; <b>Distributed Session Store:</b> Transition in-memory session dictionary to Redis with TTL expiration for horizontal auto-scaling across container replicas.", bullet_style))
    story.append(Paragraph("&bull; <b>Real-Time Inventory CDC:</b> Ingest continuous lot updates (bids, yard arrivals, title changes) via Kafka / AWS Kinesis change-data-capture pipelines.", bullet_style))
    story.append(Paragraph("&bull; <b>Production Guardrails:</b> Add prompt injection firewalls (NeMo Guardrails), rate limiting via API Gateway, and latency tracking using LangSmith / OpenTelemetry.", bullet_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"✅ Generated updated 4-page Hybrid Search PDF successfully at: {PDF_OUTPUT_PATH}")

if __name__ == "__main__":
    build_pdf()
