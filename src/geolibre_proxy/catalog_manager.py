"""Catalog Manager for GeoLibre S3 Datasets & Thematic Layer Hierarchies.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.geolibre_proxy.schemas import ProjectCatalogResponse, ThematicCategory, LayerCatalogItem


class CatalogManager:
    """Manages the S3 thematic dataset catalog and provides schema metadata for Spatial AI."""

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).resolve().parent.parent.parent / "config" / "geolibre_aura_project.json"
        self.config_path = config_path
        self._catalog_data: Dict[str, Any] = self._load_catalog()

    def _load_catalog(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"GeoLibre configuration file not found at {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_project_catalog(self) -> ProjectCatalogResponse:
        """Returns the full project catalog schema response."""
        return ProjectCatalogResponse(**self._catalog_data)

    def get_all_s3_paths(self) -> List[str]:
        """Returns a flat list of all S3 parquet paths referenced across all categories."""
        paths = []
        for category in self._catalog_data.get("categories", []):
            for layer in category.get("layers", []):
                s3_path = layer.get("s3_path")
                if s3_path and s3_path not in paths:
                    paths.append(s3_path)
        return paths

    def get_schema_summary_for_prompt(self) -> str:
        """Generates a markdown table schema summary for injection into the LLM system prompt."""
        summary = ["### S3 Spatial Datasets (Zero-Copy Single Source of Truth):\n"]
        for cat in self._catalog_data.get("categories", []):
            summary.append(f"#### Category: {cat['name']}")
            for lyr in cat.get("layers", []):
                s3_path = lyr.get("s3_path", "")
                props = ", ".join(lyr.get("popup_properties", [])) or "geometry, standard_attributes"
                summary.append(f"- **Table (`{lyr['id']}`)**: `{s3_path}`")
                summary.append(f"  - Attributes: {props}")
            summary.append("")
        return "\n".join(summary)
