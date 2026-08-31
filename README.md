# Copart Conversational Hybrid Search

A full-stack conversational vehicle search platform for Copart's salvage and used inventory, powered by **Hybrid Search (Structured SQL + Semantic RAG & Knowledge Base)** and multi-turn conversational dialogue.

---

## Architecture Overview

```
User Query: "Show me Toyota SUVs under $15k that are easy to fix with no airbag damage"
                                      │
                     ┌────────────────┴────────────────┐
                     ▼                                 ▼
      [ Structured SQL Filters ]             [ Semantic RAG Search ]
      • Make: Toyota                         • Query: "easy fix DIY airbags intact"
      • Body: SUV                            • Target: Mechanic notes & adjuster remarks
      • Max Price: $15,000                   • Scoring: FTS5 BM25 Semantic Relevance
                     │                                 │
                     └────────────────┬────────────────┘
                                      │
                                      ▼
                        [ Hybrid SQL Execution Engine ]
                Filters by hard constraints (Price, Make, State)
               + Ranks by semantic similarity of inspector notes
                                      │
                                      ▼
                      [ Enriched UI with Inspector Notes ]
```

---

## Key Features

1. **Hybrid Search Architecture**:
   * **Deterministic SQL Filters**: Fast B-Tree indexed queries for hard bounds (`price <= 15000`, `make = 'Toyota'`, `location_state = 'TX'`).
   * **Semantic / Inspector Notes RAG**: Evaluates unstructured mechanic notes (e.g., *"airbags intact"*, *"easy DIY bolt-on fix"*, *"light hail for PDR"*, *"freshwater only"*).
2. **Copart Policy Knowledge Base (RAG)**:
   * Instant retrieval and guidance on Copart auction conditions (*Run & Drive* vs *Enhanced Vehicle*), *Salvage Title vs Clean Title*, broker licensing, and *Paintless Dent Repair (PDR)*.
3. **Multi-Turn Conversational Memory**:
   * Accumulates constraints across turns (*"Toyota SUVs"* &rarr; *"Under $15k"*).
   * Overrides specific fields seamlessly (*"Actually show Honda instead"*).
   * Resets cleanly on demand (*"Start over"*).
4. **Pluggable LLM Integration with Fallback**:
   * Supports **Google Gemini 3.6 Flash** (Google Generative Language API) and **OpenAI GPT-4o-mini** (`openai`) tool calling.
   * Built-in zero-cost local NLP fallback engine for instant testing without API keys.
5. **Modern React Frontend**:
   * Dark-mode glassmorphism design with live active filter badges, suggestion chips, and vehicle cards with **Inspector Note badges**.

---

## Project Structure

```
copart project/
├── backend/
│   ├── main.py          # FastAPI app: /chat, /vehicles, /filter-options, /health
│   ├── agent.py         # LLM agent with tool calling + Knowledge Base RAG
│   ├── inventory.py     # Hybrid SQL + FTS5 BM25 ranking query engine
│   ├── session.py       # Multi-turn conversation state & filter merging
│   ├── models.py        # Pydantic schemas (Vehicle, VehicleFilters, ChatRequest/Response)
│   ├── seed_data.py     # 500-vehicle generator with inspector notes & Copart policies
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx                        # Root coordinator layout
│   │   ├── index.css                      # Design system & dark-mode styling
│   │   └── components/
│   │       ├── ChatInterface.jsx          # Interactive dialogue panel & suggestion chips
│   │       ├── VehicleCard.jsx            # Card with photo, price, and Inspector Notes
│   │       ├── FilterPanel.jsx            # Active structured & semantic filter tags
│   │       └── ConversationBubble.jsx     # User, bot, and typing bubbles
│   ├── index.html
│   ├── vite.config.js   # Fast HMR & dev API proxy to backend :8000
│   └── package.json
├── docs/                # Application screenshots
├── Copart_Conversational_Search_Documentation.pdf  # Comprehensive 4-page PDF guide
└── README.md
```

---

## Quick Start & Setup

### Prerequisites
* Python 3.10+ (tested on Python 3.13)
* Node.js 18+

### Step 1: Start Backend Server
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Seed the database (500 vehicles + inspector notes + knowledge base)
python3 seed_data.py

# (Optional) Set your API key in .env
cp .env.example .env
# Edit .env: set GEMINI_API_KEY=AIza... or OPENAI_API_KEY=sk-...

# Launch FastAPI
uvicorn main:app --reload --port 8000
```
Backend API will be live at: **http://localhost:8000** (Swagger documentation: **http://localhost:8000/docs**)

---

### Step 2: Start Frontend Application
In a new terminal:
```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
Open **http://localhost:5173** in your browser.

---

## Step-by-Step Testing & Verification

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Test Hybrid Search (Structured SQL + Semantic Mechanic Notes)
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me Toyota SUVs easy to fix with no airbag damage"}' | python3 -m json.tool
```

### 3. Test Copart Policy Knowledge RAG
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What does Enhanced Vehicle mean at Copart?"}' | python3 -m json.tool
```

### 4. Test Salvage Title Policy Advisory
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the difference between Salvage Title and Clean Title?"}' | python3 -m json.tool
```

### 5. Test Multi-Turn Filter Refinement
```bash
# Turn 1: Initial query & capture session ID
SESSION=$(curl -s -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"message": "Show me Ford trucks"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")

# Turn 2: Add price constraint (retains Ford & truck)
curl -s -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d "{\"message\": \"Under \$15000\", \"session_id\": \"$SESSION\"}" | python3 -m json.tool

# Turn 3: Switch make to Chevrolet (replaces make, retains truck & price)
curl -s -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d "{\"message\": \"Actually make it Chevrolet\", \"session_id\": \"$SESSION\"}" | python3 -m json.tool
```

---

## Production Evolution (Interview Discussion Points)

1. **Database & Scale**: Migrate SQLite to PostgreSQL with `pgvector` or OpenSearch for hybrid semantic vector embeddings + structured filtering across millions of vehicles.
2. **Distributed Sessions**: Move in-memory session dictionary to Redis clusters with TTL expiration for horizontal scalability.
3. **Live Inventory CDC**: Ingest real-time yard arrivals, bid increments, and title status changes via Apache Kafka / AWS Kinesis pipelines.
4. **Safety & Observability**: Add prompt injection firewalls (NeMo Guardrails), rate limiting via API Gateway, and latency tracking using LangSmith / OpenTelemetry.

---

## Documentation PDF
A 4-page guide is available at: [`Copart_Conversational_Search_Documentation.pdf`](./Copart_Conversational_Search_Documentation.pdf).
