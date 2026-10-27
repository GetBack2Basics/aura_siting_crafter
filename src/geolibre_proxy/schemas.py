"""Pydantic schemas for the GeoLibre Spatial AI Proxy.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SpatialQueryRequest(BaseModel):
    query: Optional[str] = Field(None, description="Natural language spatial question or filtering criteria")
    prompt: Optional[str] = Field(None, description="Alias for natural language question or prompt")
    region: Optional[str] = Field("national", description="Target spatial region (e.g. national, hunter, latrobe, gladstone)")
    active_layers: Optional[List[str]] = Field(default_factory=list, description="IDs of active layers in GeoLibre viewport")
    openrouter_api_key: Optional[str] = Field(None, description="Optional user-provided OpenRouter BYOK key")
    model: Optional[str] = Field("gemini-2.5-flash", description="LLM model identifier")

    @property
    def effective_query(self) -> str:
        return (self.query or self.prompt or "").strip()


class SpatialQueryResponse(BaseModel):
    natural_query: str
    translated_sql: str
    target_s3_tables: List[str]
    explanation: str
    execution_engine: str = "DuckDB-WASM"
    suggested_viewport: Optional[Dict[str, Any]] = None
    clarifying_questions: List[str] = Field(
        default_factory=list,
        description="Clarifying questions or suggestions to resolve ambiguity before execution"
    )
    issues_detected: List[str] = Field(
        default_factory=list,
        description="Potential issues, constraints conflicts, or edge cases detected in query"
    )
    recommendations: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Actionable query recommendations with label and sql_patch"
    )
    confidence_score: float = Field(
        1.0,
        description="Confidence score between 0.0 and 1.0"
    )


class LayerCatalogItem(BaseModel):
    id: str
    name: str
    type: str
    source_type: str
    s3_path: str
    stream_url: Optional[str] = None
    minzoom: Optional[int] = None
    visible: bool = True
    paint: Optional[Dict[str, Any]] = None
    filter: Optional[List[Any]] = None
    popup_properties: Optional[List[str]] = None


class ThematicCategory(BaseModel):
    id: str
    name: str
    description: str
    expanded_by_default: bool = False
    layers: List[LayerCatalogItem]


class ProjectCatalogResponse(BaseModel):
    project_name: str
    version: str
    storage_root: str
    default_view: Dict[str, Any]
    basemap: Dict[str, Any]
    theme_tokens: Dict[str, str]
    persona_presets: Dict[str, Any]
    categories: List[ThematicCategory]
