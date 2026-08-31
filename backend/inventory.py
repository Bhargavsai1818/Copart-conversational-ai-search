"""
inventory.py — SQLite query layer with Hybrid Search (SQL + Semantic / FTS5 BM25) and Copart Knowledge RAG.

Design decisions:
- Uses parameterized queries throughout (SQL injection safe)
- Hybrid ranking: Combines strict SQL filters (price, year, make) with FTS5 BM25 semantic scoring on inspector notes
- Knowledge Base RAG: Retrieves relevant Copart policies, title rules, and auction guidelines
- Returns structured Vehicle objects via Pydantic
"""
from __future__ import annotations
import sqlite3
import os
import re
from typing import Any, Optional

from models import Vehicle, VehicleFilters

DB_PATH = os.path.join(os.path.dirname(__file__), "inventory.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _clean_fts_query(query: str) -> str:
    """Sanitize free-text user search for SQLite FTS5 syntax."""
    words = re.findall(r'\b[a-zA-Z0-9_]+\b', query)
    if not words:
        return ""
    # Filter common stop words
    stopwords = {"the", "a", "an", "and", "or", "in", "on", "at", "for", "with", "that", "this", "is", "are"}
    meaningful = [w for w in words if w.lower() not in stopwords]
    if not meaningful:
        meaningful = words
    # Join with OR or space for BM25 ranking
    return " OR ".join(f'"{w}"' for w in meaningful)


def search_vehicles(filters: VehicleFilters) -> tuple[list[Vehicle], int]:
    """
    Execute a Hybrid Query combining hard SQL constraints with semantic/full-text matching.

    Returns (vehicles, total_count).
    """
    conn = _get_conn()
    try:
        clauses: list[str] = []
        params: list[Any] = []
        join_fts = False
        fts_match_query = ""

        # Check for semantic query
        if filters.semantic_query:
            clean_q = _clean_fts_query(filters.semantic_query)
            if clean_q:
                join_fts = True
                fts_match_query = clean_q
                clauses.append("vehicles_fts MATCH ?")
                params.append(fts_match_query)

        # Standard Structured SQL Filters
        if filters.make:
            clauses.append("LOWER(v.make) = LOWER(?)")
            params.append(filters.make)

        if filters.model:
            clauses.append("LOWER(v.model) = LOWER(?)")
            params.append(filters.model)

        if filters.year_min:
            clauses.append("v.year >= ?")
            params.append(filters.year_min)

        if filters.year_max:
            clauses.append("v.year <= ?")
            params.append(filters.year_max)

        if filters.price_min:
            clauses.append("v.price >= ?")
            params.append(filters.price_min)

        if filters.price_max:
            clauses.append("v.price <= ?")
            params.append(filters.price_max)

        if filters.mileage_max:
            clauses.append("v.mileage <= ?")
            params.append(filters.mileage_max)

        if filters.color:
            clauses.append("LOWER(v.color) = LOWER(?)")
            params.append(filters.color)

        if filters.body_type:
            clauses.append("v.body_type = ?")
            params.append(filters.body_type.lower())

        if filters.condition:
            placeholders = ",".join("?" for _ in filters.condition)
            clauses.append(f"v.condition IN ({placeholders})")
            params.extend(filters.condition)

        if filters.damage_type:
            clauses.append("v.damage_type = ?")
            params.append(filters.damage_type.lower())

        if filters.location_state:
            clauses.append("UPPER(v.location_state) = UPPER(?)")
            params.append(filters.location_state)

        if filters.transmission:
            clauses.append("v.transmission = ?")
            params.append(filters.transmission.lower())

        if filters.fuel_type:
            clauses.append("v.fuel_type = ?")
            params.append(filters.fuel_type.lower())

        from_clause = "vehicles v"
        if join_fts:
            from_clause = "vehicles v JOIN vehicles_fts ON v.id = vehicles_fts.rowid"

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        # Determine Ordering (BM25 relevance score or structured sorting)
        if join_fts and (not filters.sort_by or filters.sort_by == "relevance"):
            order = "bm25(vehicles_fts) ASC, v.price ASC"
        else:
            sort_map = {
                "price_asc": "v.price ASC",
                "price_desc": "v.price DESC",
                "year_asc": "v.year ASC",
                "year_desc": "v.year DESC",
                "mileage_asc": "v.mileage ASC",
                "mileage_desc": "v.mileage DESC",
                "relevance": "v.price ASC"
            }
            order = sort_map.get(filters.sort_by or "price_asc", "v.price ASC")

        count_sql = f"SELECT COUNT(*) as cnt FROM {from_clause} {where}"
        total = conn.execute(count_sql, params).fetchone()["cnt"]

        # If zero matches with strict semantic search, fallback to structured filters only
        if total == 0 and join_fts:
            filters_no_semantic = filters.model_copy(update={"semantic_query": None})
            return search_vehicles(filters_no_semantic)

        data_sql = f"""
            SELECT v.* FROM {from_clause}
            {where}
            ORDER BY {order}
            LIMIT ?
        """
        rows = conn.execute(data_sql, params + [filters.limit]).fetchall()
        vehicles = [Vehicle(**dict(row)) for row in rows]
        return vehicles, total
    finally:
        conn.close()


def query_knowledge_base(query: str) -> Optional[dict[str, str]]:
    """
    RAG lookup across Copart policies, title rules, and auction guidelines.
    Returns matching policy topic and content if found.
    """
    conn = _get_conn()
    try:
        clean_q = _clean_fts_query(query)
        if not clean_q:
            return None
        sql = """
            SELECT topic, content
            FROM copart_knowledge_fts
            WHERE copart_knowledge_fts MATCH ?
            ORDER BY rank
            LIMIT 1
        """
        row = conn.execute(sql, [clean_q]).fetchone()
        if row:
            return {"topic": row["topic"], "content": row["content"]}
        return None
    except Exception:
        return None
    finally:
        conn.close()



def get_vehicle_by_id(vehicle_id: int) -> Optional[Vehicle]:
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,)).fetchone()
        return Vehicle(**dict(row)) if row else None
    finally:
        conn.close()


def get_filter_options() -> dict[str, Any]:
    """Return available filter facets for the UI."""
    conn = _get_conn()
    try:
        makes = [r[0] for r in conn.execute("SELECT DISTINCT make FROM vehicles ORDER BY make").fetchall()]
        states = [r[0] for r in conn.execute("SELECT DISTINCT location_state FROM vehicles ORDER BY location_state").fetchall()]
        colors = [r[0] for r in conn.execute("SELECT DISTINCT color FROM vehicles ORDER BY color").fetchall()]
        body_types = [r[0] for r in conn.execute("SELECT DISTINCT body_type FROM vehicles ORDER BY body_type").fetchall()]
        price_range = conn.execute("SELECT MIN(price), MAX(price) FROM vehicles").fetchone()
        year_range = conn.execute("SELECT MIN(year), MAX(year) FROM vehicles").fetchone()

        return {
            "makes": makes,
            "states": states,
            "colors": colors,
            "body_types": body_types,
            "price_range": {"min": price_range[0], "max": price_range[1]},
            "year_range": {"min": year_range[0], "max": year_range[1]},
        }
    finally:
        conn.close()
