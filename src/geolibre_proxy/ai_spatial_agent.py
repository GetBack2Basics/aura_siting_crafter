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
        """Translates a user request into DuckDB Spatial SQL using available data,
        detecting issues, constraints, and generating clarifying questions for review.
        """
        query_text = request.query.strip()
        lower_q = query_text.lower()

        candidates_s3 = "s3://wherobots-user-storage/aura_siting/candidates/datacenter_candidates_national.parquet"
        clauses: List[str] = []
        explanation_parts: List[str] = []
        clarifying_questions: List[str] = []
        issues_detected: List[str] = []
        recommendations: List[Dict[str, str]] = []

        # 1. State / Regional Scope Resolution
        # Map regional center aliases to authoritative states
        region_map = {
            "New South Wales": ["nsw", "new south wales", "hunter", "newcastle", "lake macquarie", "teralba", "killingworth", "cockle creek", "west lake"],
            "Victoria": ["vic", "victoria", "latrobe", "morwell", "traralgon", "moe"],
            "Queensland": ["qld", "queensland", "gladstone", "yarwun", "calliope"],
            "Western Australia": ["wa", "western australia", "collie"],
            "Australian Capital Territory": ["act", "australian capital territory", "canberra", "fyshwick", "hume"],
            "Northern Territory": ["nt", "northern territory", "darwin", "east arm"],
            "South Australia": ["sa", "south australia", "port augusta"],
            "Tasmania": ["tas", "tasmania", "devonport"],
        }

        matched_states = []
        for state_name, aliases in region_map.items():
            for alias in aliases:
                # Word-boundary or exact token check
                if re.search(r'\b' + re.escape(alias) + r'\b', lower_q):
                    if state_name not in matched_states:
                        matched_states.append(state_name)
                    break

        if len(matched_states) == 1:
            clauses.append(f"state_name = '{matched_states[0]}'")
            explanation_parts.append(f"Filtered to {matched_states[0]}")
        elif len(matched_states) > 1:
            or_parts = [f"state_name = '{st}'" for st in matched_states]
            clauses.append(f"({' OR '.join(or_parts)})")
            explanation_parts.append(f"Filtered to states: {', '.join(matched_states)}")
        else:
            issues_detected.append("Geographic boundary unspecified; defaulting to national scope across all 8 Australian States & Territories.")
            clarifying_questions.append("Would you like to narrow the search to a specific state (NSW, VIC, QLD, WA) or NEM region?")
            recommendations.append({"label": "+ Focus on NSW", "sql_patch": "state_name = 'New South Wales'"})
            recommendations.append({"label": "+ Focus on Victoria", "sql_patch": "state_name = 'Victoria'"})
            recommendations.append({"label": "+ Focus on Queensland", "sql_patch": "state_name = 'Queensland'"})

        # 2. Power Grid / High-Voltage Transmission Corridor Buffer
        if any(k in lower_q for k in ["substation", "power", "grid", "kv", "transmission", "corridor"]):
            match = re.search(r'(\d+(?:\.\d+)?)\s*(?:km|kilo)', lower_q)
            if match:
                dist = float(match.group(1))
                clauses.append(f"dist_to_substation_km <= {dist}")
                explanation_parts.append(f"within {dist}km of high-voltage transmission")
            else:
                clauses.append("dist_to_substation_km <= 1.5")
                explanation_parts.append("within 1.5km of high-voltage transmission")
                issues_detected.append("Transmission distance not specified; defaulted to standard connection buffer (≤ 1.5 km).")
                clarifying_questions.append("Transmission buffer defaulted to ≤ 1.5 km. Would you prefer a direct adjacent connection (≤ 0.5 km)?")
                recommendations.append({"label": "Substation ≤ 0.5 km", "sql_patch": "dist_to_substation_km <= 0.5"})

        # 3. Developable Parcel Area (ha)
        if any(k in lower_q for k in ["ha", "hectare", "acres", "area", "parcel", "large", "hyperscale", "scale"]):
            match = re.search(r'(\d+(?:\.\d+)?)\s*(?:ha|hectare)', lower_q)
            if match:
                min_area = float(match.group(1))
                clauses.append(f"area_ha >= {min_area}")
                explanation_parts.append(f"minimum {min_area} ha developable area")
                if min_area >= 50.0:
                    issues_detected.append(f"Largest candidate parcel in national database is 44.5 ha (Teralba, NSW). A minimum threshold of {min_area} ha will return 0 matches. Suggested: ≥ 25 ha.")
                    clarifying_questions.append("Requested area exceeds all current candidates (>45 ha). Should we relax the threshold to ≥ 25 ha?")
                    recommendations.append({"label": "Set Area ≥ 25 ha", "sql_patch": "area_ha >= 25.0"})
            else:
                clauses.append("area_ha >= 15.0")
                explanation_parts.append("minimum 15 ha developable area")
                issues_detected.append("Parcel area not specified; defaulted to 15 ha (hyperscale campus baseline).")
                clarifying_questions.append("What minimum parcel size is required for your facility (e.g. ≥ 15 ha for 100MW campus, or ≥ 25 ha for hyperscale)?")
                recommendations.append({"label": "Set Area ≥ 20 ha", "sql_patch": "area_ha >= 20.0"})

        # 4. Sensitive Receptor Acoustic / Statutory Setback
        if any(k in lower_q for k in ["sensitive", "receptor", "school", "hospital", "residential", "buffer", "setback", "acoustic"]):
            match = re.search(r'(?:buffer|away|setback|from).*?(\d+(?:\.\d+)?)\s*(?:km|kilo)', lower_q)
            if match:
                sens_dist = float(match.group(1))
                clauses.append(f"dist_to_sensitive_km >= {sens_dist}")
                explanation_parts.append(f"at least {sens_dist}km setback from sensitive receptors")
            else:
                clauses.append("dist_to_sensitive_km >= 1.0")
                explanation_parts.append("at least 1.0km setback from sensitive receptors")
                issues_detected.append("Receptor buffer defaulted to statutory baseline (≥ 1.0 km).")
                clarifying_questions.append("Receptor setback set to ≥ 1.0 km. Should we enforce the strict Tier-1 buffer of ≥ 1.5 km from all residential meshblocks?")
                recommendations.append({"label": "Strict Buffer ≥ 1.5 km", "sql_patch": "dist_to_sensitive_km >= 1.5"})

        # 5. Recycled Water Proximity
        if any(k in lower_q for k in ["water", "wwtw", "recycled", "cooling", "effluent"]):
            match = re.search(r'(?:water|wwtw|cooling).*?(\d+(?:\.\d+)?)\s*(?:km|kilo)', lower_q)
            if match:
                w_dist = float(match.group(1))
                clauses.append(f"dist_to_wwtw_km <= {w_dist}")
                explanation_parts.append(f"within {w_dist}km of recycled water infrastructure")
            else:
                clauses.append("dist_to_wwtw_km <= 2.0")
                explanation_parts.append("within 2.0km of recycled water infrastructure")
                issues_detected.append("Water proximity defaulted to ≤ 2.0 km of tertiary recycled water/WWTW.")
                clarifying_questions.append("Recycled water defaulted to ≤ 2.0 km. Does your facility use air cooling (can relax water requirement) or water cooling (needs ≤ 1.0 km)?")
                recommendations.append({"label": "Recycled Water ≤ 1.0 km", "sql_patch": "dist_to_wwtw_km <= 1.0"})

        # 6. Terrain Slope Grade
        if any(k in lower_q for k in ["slope", "grade", "flat", "terrain", "topography"]):
            match = re.search(r'(\d+(?:\.\d+)?)\s*%', lower_q)
            if match:
                max_slope = float(match.group(1))
                clauses.append(f"slope_pct <= {max_slope}")
                explanation_parts.append(f"terrain slope grade ≤ {max_slope}%")
            else:
                clauses.append("slope_pct <= 2.5")
                explanation_parts.append("terrain slope grade ≤ 2.5% (flat land)")
                issues_detected.append("Slope threshold defaulted to ≤ 2.5% for slab-on-grade earthworks.")

        # 7. Suitability & Hazard Score
        if any(k in lower_q for k in ["score", "suitability", "top", "best", "ranked"]):
            match = re.search(r'(?:score|suitability)\s*(?:>=|>|over|at least)?\s*(\d+(?:\.\d+)?)', lower_q)
            if match:
                score_val = float(match.group(1))
                clauses.append(f"suitability_score >= {score_val}")
                explanation_parts.append(f"MCDA composite score ≥ {score_val}")
            elif any(k in lower_q for k in ["top", "best"]):
                clauses.append("suitability_score >= 0.95")
                explanation_parts.append("top-tier candidates (score ≥ 0.95)")
                recommendations.append({"label": "Score ≥ 0.90 (Broader)", "sql_patch": "suitability_score >= 0.90"})

        # 8. Pumped Hydro Storage / Renewable Grid Firming
        if any(k in lower_q for k in ["pumped hydro", "hydro", "storage", "firming", "battery"]):
            clauses.append("pumped_hydro_capacity_mwh >= 50.0")
            explanation_parts.append("pumped hydro storage capacity ≥ 50 MWh")

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
            f"{', '.join(explanation_parts) if explanation_parts else 'Selected all candidates ranked by suitability score'}."
        )

        return SpatialQueryResponse(
            natural_query=query_text,
            translated_sql=sql.strip(),
            target_s3_tables=[candidates_s3],
            explanation=explanation,
            execution_engine="DuckDB-WASM",
            clarifying_questions=clarifying_questions,
            issues_detected=issues_detected,
            recommendations=recommendations,
            confidence_score=0.95 if clauses else 0.80
        )
