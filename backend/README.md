# Copart Conversational Hybrid Search — Backend API

FastAPI backend with **Hybrid Search (Structured SQL + Semantic RAG & Knowledge Base)**.

## Architecture
- `main.py`: API Gateway exposing `POST /chat`, `GET /vehicles`, `GET /filter-options`, `GET /health`, `DELETE /session/{id}`.
- `agent.py`: LLM agent supporting Gemini 3.6 Flash, OpenAI GPT-4o-mini, and a local rule-based Hybrid Fallback.
- `inventory.py`: SQLite query engine with B-Tree indexes, FTS5 BM25 semantic ranking, and Copart Knowledge Base retrieval.
- `session.py`: Multi-turn conversational memory & filter merging.
- `models.py`: Pydantic data schemas.
- `seed_data.py`: Generates 500 realistic vehicles with mechanic inspector notes and Copart policies.

## Setup & Running
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Seed inventory + inspector notes + knowledge base
python3 seed_data.py

# Launch server
uvicorn main:app --reload --port 8000
```

## Testing Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Hybrid search
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me Toyota SUVs easy to fix with no airbag damage"}' | python3 -m json.tool

# Policy RAG
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What does Enhanced Vehicle mean at Copart?"}' | python3 -m json.tool
```
