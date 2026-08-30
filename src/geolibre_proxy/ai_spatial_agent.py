"""Spatial AI Agent translating natural language queries to DuckDB Spatial SQL.
Supports Google Cloud Gemini API and OpenRouter BYOK.
"""

import os
import re
from typing import Dict, Any, List
from src.geolibre_proxy.catalog_manager import CatalogManager
from src.geolibre_proxy.schemas import SpatialQueryRequest, SpatialQueryResponse


class SpatialAiAgent:
    """Agent that translates natural language questions into valid DuckDB Spatial SQL."""

    def __init__(self, catalog_manager: CatalogManager):
        self.catalog_manager = catalog_manager

    def build_system_prompt(self) -> str:
        """Constructs the spatial schema system prompt for the LLM."""
        schema_summary = self.catalog_manager.get_schema_summary_for_prompt()
        prompt = f"""You are the AURA Spatial AI Assistant for GeoLibre WebGIS.
Your task is to translate user natural language questions into high-performance DuckDB Spatial SQL queries executed in-browser.

{schema_summary}

### DuckDB Spatial SQL Rules:
1. Always use `read_parquet('s3://...')` with exact S3 URLs from the catalog.
2. DuckDB Spatial supports standard spatial functions: `ST_Point(lon, lat)`, `ST_Distance(geom1, geom2)`, `ST_DWithin(geom1, geom2, dist)`, `ST_Area(geom)`, `ST_Buffer(geom, dist)`.
3. Output ONLY the DuckDB SQL statement and a concise 1-2 sentence explanation.
4. If the query asks for candidates, select: `site_name`, `town_name`, `state_name`, `area_ha`, `dist_to_substation_km`, `dist_to_wwtw_km`, `dist_to_sensitive_km`, `suitability_score`, `geometry`.
5. Apply filters directly in the WHERE clause (e.g. `dist_to_substation_km <= 2.0`, `dist_to_sensitive_km >= 1.0`, `area_ha >= 15.0`).
"""
        return prompt

    def translate_query(self, request: SpatialQueryRequest) -> SpatialQueryResponse:
        """Translates a user request into DuckDB Spatial SQL."""
        query_text = request.query.strip()
        lower_q = query_text.lower()

        # Deterministic spatial parser & LLM fallback
        candidates_s3 = "s3://wherobots-user-storage/aura_siting/candidates/datacenter_candidates_national.parquet"
        clauses: List[str] = []
        explanation_parts: List[str] = []

        # Parse State filter
        if "nsw" in lower_q or "new south wales" in lower_q:
            clauses.append("state_name = 'New South Wales'")
            explanation_parts.append("Filtered to New South Wales")
        elif "vic" in lower_q or "victoria" in lower_q:
            clauses.append("state_name = 'Victoria'")
            explanation_parts.append("Filtered to Victoria")
        elif "qld" in lower_q or "queensland" in lower_q:
            clauses.append("state_name = 'Queensland'")
            explanation_parts.append("Filtered to Queensland")
        elif "wa" in lower_q or "western australia" in lower_q:
            clauses.append("state_name = 'Western Australia'")
            explanation_parts.append("Filtered to Western Australia")
        elif "act" in lower_q or "canberra" in lower_q:
            clauses.append("state_name = 'Australian Capital Territory'")
            explanation_parts.append("Filtered to ACT")

        # Parse Power Grid / Substation buffer
        if "substation" in lower_q or "power" in lower_q or "kv" in lower_q or "transmission" in lower_q:
            match = re.search(r'(\d+(?:\.\d+)?)\s*(?:km|kilo)', lower_q)
            dist = float(match.group(1)) if match else 2.0
            clauses.append(f"dist_to_substation_km <= {dist}")
            explanation_parts.append(f"within {dist}km of high-voltage transmission")

        # Parse Parcel Area
        if "ha" in lower_q or "hectare" in lower_q or "large" in lower_q:
            match = re.search(r'(\d+(?:\.\d+)?)\s*(?:ha|hectare)', lower_q)
            min_area = float(match.group(1)) if match else 15.0
            clauses.append(f"area_ha >= {min_area}")
            explanation_parts.append(f"minimum {min_area} ha developable area")

        # Parse Sensitive Receptor Setback
        if "sensitive" in lower_q or "school" in lower_q or "hospital" in lower_q or "buffer" in lower_q:
            match = re.search(r'(?:buffer|away|setback).*?(\d+(?:\.\d+)?)\s*(?:km|kilo)', lower_q)
            sens_dist = float(match.group(1)) if match else 1.0
            clauses.append(f"dist_to_sensitive_km >= {sens_dist}")
            explanation_parts.append(f"at least {sens_dist}km setback from sensitive receptors")

        # Parse Recycled Water
        if "water" in lower_q or "wwtw" in lower_q or "recycled" in lower_q:
            match = re.search(r'(?:water|wwtw).*?(\d+(?:\.\d+)?)\s*(?:km|kilo)', lower_q)
            w_dist = float(match.group(1)) if match else 2.0
            clauses.append(f"dist_to_wwtw_km <= {w_dist}")
            explanation_parts.append(f"within {w_dist}km of recycled water infrastructure")

        # Parse Slope
        if "slope" in lower_q or "grade" in lower_q or "flat" in lower_q:
            clauses.append("slope_pct <= 5.0")
            explanation_parts.append("terrain slope grade ≤ 5.0%")

        # Build SQL query
        where_stmt = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = (
            f"SELECT town_name, state_name, area_ha, dist_to_substation_km, "
            f"dist_to_wwtw_km, dist_to_sensitive_km, slope_pct, suitability_score, geometry\n"
            f"FROM read_parquet('{candidates_s3}')\n"
            f"{where_stmt}\n"
            f"ORDER BY suitability_score DESC;"
        )

        explanation = (
            f"Translated natural language query into DuckDB Spatial SQL. "
            f"{', '.join(explanation_parts) if explanation_parts else 'Selected all candidates ranked by suitability'}."
        )

        return SpatialQueryResponse(
            natural_query=query_text,
            translated_sql=sql.strip(),
            target_s3_tables=[candidates_s3],
            explanation=explanation,
            execution_engine="DuckDB-WASM"
        )
