"""
main.py — FastAPI application entry point for Copart Conversational Hybrid Search.

Architecture:
  POST /chat           — Multi-turn conversational search with Hybrid SQL + Semantic RAG
  GET  /vehicles       — Direct programmatic vehicle search
  GET  /filter-options — Available facets for the UI
  DELETE /session/{id} — Clear a conversation session
"""
from __future__ import annotations
import os
from typing import Any, Optional

# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException, Query
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

from models import ChatRequest, ChatResponse, Vehicle, VehicleFilters
from inventory import search_vehicles, get_filter_options, get_vehicle_by_id, query_knowledge_base
from session import get_or_create, delete_session, merge_filters
from agent import run_agent, SYSTEM_PROMPT
from seed_data import seed_database, DB_PATH

load_dotenv()

# ─── App init ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Copart Conversational Hybrid Search API",
    description="Natural-language vehicle inventory search powered by Hybrid SQL + Semantic RAG",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Seed the database on first run if it doesn't exist."""
    if not os.path.exists(DB_PATH):
        print("🌱 Seeding vehicle inventory database...")
        seed_database()
    else:
        print(f"✅ Database found at {DB_PATH}")


# ─── Chat endpoint (primary) ─────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Multi-turn conversational search endpoint with Hybrid SQL + Semantic RAG.
    """
    session = get_or_create(request.session_id)

    # Build message list with system prompt at front
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(session.messages)
    messages.append({"role": "user", "content": request.message})

    # Run LLM agent (returns conversational reply, tool filter args, and policy knowledge)
    reply, new_filter_args, policy_knowledge = run_agent(messages)

    # Merge new filters into session state
    if new_filter_args:
        session.active_filters = merge_filters(session.active_filters, new_filter_args)

    # Execute Hybrid Search (SQL + Semantic BM25)
    active = session.active_filters
    filters = VehicleFilters(
        make=active.get("make"),
        model=active.get("model"),
        year_min=active.get("year_min"),
        year_max=active.get("year_max"),
        price_min=active.get("price_min"),
        price_max=active.get("price_max"),
        mileage_max=active.get("mileage_max"),
        color=active.get("color"),
        body_type=active.get("body_type"),
        condition=active.get("condition"),
        damage_type=active.get("damage_type"),
        location_state=active.get("location_state"),
        transmission=active.get("transmission"),
        fuel_type=active.get("fuel_type"),
        semantic_query=active.get("semantic_query"),
        sort_by=active.get("sort_by", "relevance"),
        limit=12,
    )
    vehicles, total = search_vehicles(filters)

    if not reply:
        reply = f"I found {total} vehicles matching your criteria."

    # If policy knowledge is retrieved, append it gracefully to the message
    combined_message = reply
    if policy_knowledge and policy_knowledge not in reply:
        combined_message = f"{reply}\n\n{policy_knowledge}"

    # Update session message history
    session.messages.append({"role": "user", "content": request.message})
    session.messages.append({"role": "assistant", "content": combined_message})
    session.messages = session.messages[-40:]

    return ChatResponse(
        session_id=session.session_id,
        assistant_message=combined_message,
        vehicles=vehicles,
        active_filters=session.active_filters,
        total_matches=total,
        policy_knowledge=policy_knowledge,
    )


# ─── Direct vehicle search ────────────────────────────────────────────────────

@app.get("/vehicles", response_model=dict)
async def get_vehicles(
    make: Optional[str] = None,
    model: Optional[str] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    mileage_max: Optional[int] = None,
    color: Optional[str] = None,
    body_type: Optional[str] = None,
    condition: Optional[str] = Query(None, description="Comma-separated condition codes"),
    damage_type: Optional[str] = None,
    location_state: Optional[str] = None,
    transmission: Optional[str] = None,
    fuel_type: Optional[str] = None,
    semantic_query: Optional[str] = None,
    sort_by: Optional[str] = "price_asc",
    limit: int = Query(12, le=50),
):
    """Programmatic vehicle search with query parameters."""
    condition_list = condition.split(",") if condition else None
    filters = VehicleFilters(
        make=make, model=model, year_min=year_min, year_max=year_max,
        price_min=price_min, price_max=price_max, mileage_max=mileage_max,
        color=color, body_type=body_type, condition=condition_list,
        damage_type=damage_type, location_state=location_state,
        transmission=transmission, fuel_type=fuel_type,
        semantic_query=semantic_query, sort_by=sort_by, limit=limit,
    )
    vehicles, total = search_vehicles(filters)
    return {"vehicles": vehicles, "total": total}


@app.get("/vehicles/{vehicle_id}", response_model=Vehicle)
async def get_vehicle(vehicle_id: int):
    v = get_vehicle_by_id(vehicle_id)
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return v


# ─── Filter options ───────────────────────────────────────────────────────────

@app.get("/filter-options")
async def filter_options() -> dict[str, Any]:
    """Return available facet values for the search UI."""
    return get_filter_options()


# ─── Session management ───────────────────────────────────────────────────────

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    deleted = delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session cleared"}


# ─── Health check ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "db_exists": os.path.exists(DB_PATH)}
