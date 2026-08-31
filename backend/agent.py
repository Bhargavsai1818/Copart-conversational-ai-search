"""
agent.py — LLM agent with structured tool-calling for Hybrid Vehicle Search & Copart Knowledge RAG.

Supports both OpenAI (GPT-4o-mini) and Google Gemini (3.6 Flash / 3.x).
The LLM is given a `search_vehicles` tool with typed parameters; it calls the tool
to extract structured filters + semantic inspector search queries from free-form user input.
"""
from __future__ import annotations
import json
import os
import re
from typing import Any

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

from models import VehicleFilters
from inventory import query_knowledge_base

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()

# ─── Tool / Function definition (provider-agnostic schema) ────────────────────

SEARCH_TOOL_SCHEMA = {
    "name": "search_vehicles",
    "description": (
        "Search the Copart vehicle inventory with structured filters and semantic criteria. "
        "Call this whenever the user asks to find, show, filter, or refine vehicles. "
        "Extract both hard structured filters (make, price, year) and subjective semantic queries (e.g. 'easy to fix', 'no airbag damage', 'light hail for PDR'). "
        "To clear all filters and start fresh, set clear_all=true."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "make": {"type": "string", "description": "Vehicle manufacturer, e.g. Toyota"},
            "model": {"type": "string", "description": "Vehicle model, e.g. Camry"},
            "year_min": {"type": "integer", "description": "Earliest model year"},
            "year_max": {"type": "integer", "description": "Latest model year"},
            "price_min": {"type": "number", "description": "Minimum price in USD"},
            "price_max": {"type": "number", "description": "Maximum price in USD"},
            "mileage_max": {"type": "integer", "description": "Maximum odometer reading in miles"},
            "color": {"type": "string", "description": "Exterior color, e.g. blue"},
            "body_type": {
                "type": "string",
                "enum": ["sedan", "suv", "truck", "coupe", "van", "wagon", "convertible", "hatchback"],
            },
            "condition": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["run_and_drive", "enhanced_vehicle", "stationary", "parts_only"],
                },
                "description": "Vehicle condition codes",
            },
            "damage_type": {
                "type": "string",
                "enum": [
                    "front_end", "rear_end", "hail", "flood", "fire",
                    "rollover", "mechanical", "vandalism", "minor_dents", "side", "top_roof",
                ],
            },
            "location_state": {"type": "string", "description": "Two-letter US state, e.g. TX"},
            "transmission": {"type": "string", "enum": ["automatic", "manual"]},
            "fuel_type": {"type": "string", "enum": ["gasoline", "diesel", "hybrid", "electric"]},
            "semantic_query": {
                "type": "string",
                "description": "Semantic search keywords for mechanic/adjuster notes (e.g. 'easy to fix', 'airbags intact', 'light hail for PDR', 'clean interior', 'freshwater')",
            },
            "sort_by": {
                "type": "string",
                "enum": ["price_asc", "price_desc", "year_asc", "year_desc",
                         "mileage_asc", "mileage_desc", "relevance"],
            },
            "clear_all": {
                "type": "boolean",
                "description": "Set true to reset all previous filters and start a new search",
            },
        },
        "required": [],
    },
}

SYSTEM_PROMPT = """You are CopartBot, an intelligent AI vehicle search and advisory assistant for Copart's salvage and used vehicle marketplace.

Your capabilities:
1. Hybrid Vehicle Search: Understand natural language vehicle requirements and call the `search_vehicles` tool with both structured parameters and semantic queries (for technician notes).
2. Copart Knowledge & Advisory: Explain salvage titles, auction conditions (Run & Drive vs Enhanced), bidding without a dealer license, and Paintless Dent Repair (PDR).

Guidelines:
- Always call `search_vehicles` when the user wants to find, filter, or refine vehicles.
- For subjective repair cues (e.g. "easy to fix", "no airbag damage", "minor fender scrape", "hail for PDR"), populate `semantic_query`.
- In multi-turn conversations, preserve existing filters unless the user explicitly asks to change or reset them.
- If the user asks about Copart policies or title types, provide clear, authoritative guidance.
"""


# ─── OpenAI Backend ──────────────────────────────────────────────────────────

def _run_openai(messages: list[dict]) -> tuple[str, dict[str, Any] | None, str | None]:
    # pyrefly: ignore [missing-import]
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    tools = [{
        "type": "function",
        "function": SEARCH_TOOL_SCHEMA,
    }]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    message = response.choices[0].message
    tool_filters: dict[str, Any] | None = None

    if message.tool_calls:
        call = message.tool_calls[0]
        tool_filters = json.loads(call.function.arguments)
        messages.append(message.model_dump())
        messages.append({
            "role": "tool",
            "tool_call_id": call.id,
            "content": "Filters extracted successfully. Results will be returned.",
        })
        follow_up = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
        )
        reply = follow_up.choices[0].message.content or ""
    else:
        reply = message.content or ""

    # Check for policy RAG
    last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    knowledge = query_knowledge_base(last_user)
    knowledge_text = f"**Copart Info ({knowledge['topic']}):** {knowledge['content']}" if knowledge else None

    return reply, tool_filters, knowledge_text


# ─── Gemini Backend ──────────────────────────────────────────────────────────

def _run_gemini(messages: list[dict]) -> tuple[str, dict[str, Any] | None, str | None]:
    import requests
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    props = SEARCH_TOOL_SCHEMA["parameters"]["properties"]
    gemini_props = {}
    for pname, pdef in props.items():
        ptype = pdef.get("type", "string")
        if ptype == "array":
            gemini_props[pname] = {"type": "ARRAY", "items": {"type": "STRING"}, "description": pdef.get("description", "")}
        elif ptype == "integer":
            gemini_props[pname] = {"type": "INTEGER", "description": pdef.get("description", "")}
        elif ptype == "number":
            gemini_props[pname] = {"type": "NUMBER", "description": pdef.get("description", "")}
        elif ptype == "boolean":
            gemini_props[pname] = {"type": "BOOLEAN", "description": pdef.get("description", "")}
        else:
            gemini_props[pname] = {"type": "STRING", "description": pdef.get("description", "")}

    tools = [{
        "function_declarations": [{
            "name": "search_vehicles",
            "description": SEARCH_TOOL_SCHEMA["description"],
            "parameters": {
                "type": "OBJECT",
                "properties": gemini_props,
            }
        }]
    }]

    contents = []
    system_instruction = None
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "system":
            system_instruction = {"parts": [{"text": content}]}
        elif role == "user":
            contents.append({"role": "user", "parts": [{"text": content}]})
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": content}]})

    payload: dict[str, Any] = {
        "contents": contents,
        "tools": tools,
    }
    if system_instruction:
        payload["system_instruction"] = system_instruction

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    tool_filters: dict[str, Any] | None = None
    reply = ""

    candidates = data.get("candidates", [])
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        for part in parts:
            if "functionCall" in part:
                tool_filters = part["functionCall"].get("args", {})
            if "text" in part:
                reply += part["text"]

    last_user = next((m.get("content", "") for m in reversed(messages) if m.get("role") == "user"), "")
    knowledge = query_knowledge_base(last_user)
    knowledge_text = f"**Copart Guide ({knowledge['topic']}):** {knowledge['content']}" if knowledge else None

    if not reply and tool_filters:
        reply = "I found these vehicles matching your search criteria!"

    return reply, tool_filters, knowledge_text


# ─── Hybrid Fallback Engine (No API Key) ─────────────────────────────────────

def _run_fallback(messages: list[dict]) -> tuple[str, dict[str, Any] | None, str | None]:
    """
    Rule-based Hybrid Fallback engine.
    Extracts structured fields + semantic keywords and performs Knowledge Base RAG.
    """
    last_user = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
    )
    text = last_user.lower()

    filters: dict[str, Any] = {}

    # Make detection
    makes = ["toyota", "honda", "ford", "chevrolet", "bmw", "mercedes", "audi",
             "nissan", "hyundai", "kia", "subaru", "volkswagen", "mazda", "lexus", "jeep", "dodge", "ram"]
    for m in makes:
        if m in text:
            filters["make"] = m.capitalize()
            break

    # Body type
    body_types = ["sedan", "suv", "truck", "coupe", "van", "wagon", "convertible", "hatchback"]
    for b in body_types:
        if b in text:
            filters["body_type"] = b
            break

    # Price hints
    import re
    price_match = re.search(r"under\s*\$?([\d,]+)k?", text)
    if price_match:
        val = int(price_match.group(1).replace(",", ""))
        if val < 100:
            val *= 1000
        filters["price_max"] = val

    # Year hints
    year_match = re.search(r"\b(20\d\d)\b", text)
    if year_match:
        yr = int(year_match.group(1))
        if "newer" in text or "after" in text:
            filters["year_min"] = yr
        elif "older" in text or "before" in text:
            filters["year_max"] = yr
        else:
            filters["year_min"] = yr

    # Colors
    colors = ["black", "white", "silver", "gray", "red", "blue", "green"]
    for c in colors:
        if c in text:
            filters["color"] = c.capitalize()
            break

    # Condition
    if any(w in text for w in ["run", "drive", "drivable", "running"]):
        filters["condition"] = ["run_and_drive"]

    # Semantic Inspector Queries (RAG matching)
    semantic_cues = []
    if "easy to fix" in text or "easy fix" in text or "diy" in text:
        semantic_cues.append("easy fix DIY smooth")
    if "airbag" in text or "no airbag" in text:
        semantic_cues.append("airbags intact")
    if "hail" in text or "pdr" in text or "paintless" in text:
        semantic_cues.append("hail paintless PDR")
    if "clean interior" in text or "interior" in text:
        semantic_cues.append("clean interior")
    if "flood" in text or "water" in text:
        semantic_cues.append("freshwater dry")
    if "fender" in text or "scrape" in text or "scratch" in text:
        semantic_cues.append("fender scrape cosmetic")

    if semantic_cues:
        filters["semantic_query"] = " ".join(semantic_cues)

    # Reset
    if any(w in text for w in ["start over", "reset", "clear", "new search"]):
        filters["clear_all"] = True

    # Sort
    if "cheapest" in text or "lowest price" in text:
        filters["sort_by"] = "price_asc"
    elif "most expensive" in text or "highest price" in text:
        filters["sort_by"] = "price_desc"
    elif "newest" in text or "latest" in text:
        filters["sort_by"] = "year_desc"
    elif "lowest miles" in text or "fewest miles" in text:
        filters["sort_by"] = "mileage_asc"

    # Query Knowledge RAG
    knowledge = query_knowledge_base(last_user)
    knowledge_text = f"💡 **Copart Guide ({knowledge['topic']}):** {knowledge['content']}" if knowledge else None

    reply = (
        "I performed a hybrid search matching your criteria against vehicle specifications and inspector notes! "
        "Use the filters on the right to refine further, or ask me about vehicle conditions and Copart policies."
    )
    if not filters and not knowledge_text:
        reply = (
            "Welcome to Copart vehicle search! Tell me what you're looking for — "
            "make, model, price range, condition, repair preferences (e.g. 'easy fix with no airbag damage'), or ask about auction rules."
        )

    return reply, filters if filters else None, knowledge_text


# ─── Public interface ─────────────────────────────────────────────────────────

def run_agent(messages: list[dict]) -> tuple[str, dict[str, Any] | None, str | None]:
    """
    Route to the configured LLM provider.
    Returns (assistant_reply_text, tool_filter_dict_or_None, policy_knowledge_or_None).
    """
    provider = LLM_PROVIDER
    has_openai_key = bool(os.getenv("OPENAI_API_KEY", "").strip().startswith("sk-"))
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    has_gemini_key = bool(gemini_key and not gemini_key.startswith("your_"))

    try:
        if provider == "openai" and has_openai_key:
            return _run_openai(messages)
        elif provider == "gemini" and has_gemini_key:
            return _run_gemini(messages)
        else:
            return _run_fallback(messages)
    except Exception as e:
        print(f"LLM error: {e}")
        return _run_fallback(messages)
