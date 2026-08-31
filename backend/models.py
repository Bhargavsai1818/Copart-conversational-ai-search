"""
models.py — Pydantic schemas for the Copart conversational search API with Hybrid Search support.
"""
from __future__ import annotations
from typing import Any, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


# ─── Inventory / Hybrid Search ──────────────────────────────────────────────────

class VehicleFilters(BaseModel):
    """Structured and semantic search parameters extracted by the LLM agent."""
    make: Optional[str] = Field(None, description="Vehicle make, e.g. 'Toyota'")
    model: Optional[str] = Field(None, description="Vehicle model, e.g. 'Camry'")
    year_min: Optional[int] = Field(None, description="Minimum model year, e.g. 2018")
    year_max: Optional[int] = Field(None, description="Maximum model year, e.g. 2023")
    price_min: Optional[float] = Field(None, description="Minimum price in USD")
    price_max: Optional[float] = Field(None, description="Maximum price in USD")
    mileage_max: Optional[int] = Field(None, description="Maximum odometer in miles")
    color: Optional[str] = Field(None, description="Exterior color, e.g. 'blue'")
    body_type: Optional[str] = Field(
        None,
        description="Body style: sedan, suv, truck, coupe, van, wagon, convertible, hatchback"
    )
    condition: Optional[list[str]] = Field(
        None,
        description="Condition codes: run_and_drive, enhanced_vehicle, stationary, parts_only"
    )
    damage_type: Optional[str] = Field(
        None,
        description="Primary damage, e.g. 'front_end', 'rear_end', 'flood', 'hail', 'fire', 'rollover', 'mechanical', 'vandalism', 'minor_dents'"
    )
    location_state: Optional[str] = Field(None, description="Two-letter US state code, e.g. 'TX'")
    transmission: Optional[str] = Field(None, description="'automatic' or 'manual'")
    fuel_type: Optional[str] = Field(None, description="'gasoline', 'diesel', 'hybrid', 'electric'")
    semantic_query: Optional[str] = Field(
        None,
        description="Unstructured semantic description for inspector/technician notes (e.g. 'easy to fix', 'no airbag damage', 'light hail for PDR', 'clean interior')"
    )
    sort_by: Optional[str] = Field(
        None,
        description="Sort order: price_asc, price_desc, year_asc, year_desc, mileage_asc, mileage_desc, relevance"
    )
    limit: int = Field(12, description="Max results to return (default 12)")


class Vehicle(BaseModel):
    id: int
    vin: str
    year: int
    make: str
    model: str
    trim: Optional[str]
    color: str
    body_type: str
    mileage: int
    price: float
    damage_type: str
    condition: str
    location_city: str
    location_state: str
    transmission: str
    fuel_type: str
    engine: str
    lot_number: str
    image_url: str
    inspector_notes: str = ""


# ─── Chat API ──────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # if None, a new session is created


class ChatResponse(BaseModel):
    session_id: str
    assistant_message: str
    vehicles: list[Vehicle]
    active_filters: dict[str, Any]
    total_matches: int
    policy_knowledge: Optional[str] = None
