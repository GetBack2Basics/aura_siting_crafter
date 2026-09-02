#!/usr/bin/env python3
"""
High-Resolution Spatial ETL Telemetry & Performance Logger v2 (etl_telemetry_v2.py)
AURA Siting Crafter — Multi-State Architecture.

Tracks execution duration, network throughput, projection standardization time,
coordinate cleaning counts, and compute resource lifecycle metrics.
"""

import os
import json
import time
import datetime
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIT_LOGS_DIR = os.path.join(BASE_DIR, "docs", "audit_logs")


class ETLTelemetryLoggerV2:
    """Telemetry logger tracking multi-state spatial ingestion performance and CRS conformance."""

    def __init__(self, state: str = "national", session_name: str = "v2_ingest"):
        self.state = state
        self.session_name = session_name
        self.start_wall_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.start_perf = time.perf_counter()
        self.records: List[Dict[str, Any]] = []
        self._active_timers: Dict[str, float] = {}

    def start_stage(self, stage_name: str) -> None:
        """Starts high-resolution timer for a named processing stage."""
        self._active_timers[stage_name] = time.perf_counter()

    def end_stage(self, stage_name: str, dataset_key: str, feature_count: int = 0,
                  geometry_type: str = "", crs: str = "EPSG:7844", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ends a stage timer and logs standard telemetry record."""
        start = self._active_timers.pop(stage_name, self.start_perf)
        duration_sec = round(time.perf_counter() - start, 4)

        record = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "state": self.state,
            "stage_name": stage_name,
            "dataset_key": dataset_key,
            "feature_count": feature_count,
            "geometry_type": geometry_type,
            "crs_standard": crs,
            "duration_seconds": duration_sec,
            "metadata": metadata or {}
        }
        self.records.append(record)
        return record

    def summarize(self) -> Dict[str, Any]:
        """Generates structured execution summary."""
        total_duration = round(time.perf_counter() - self.start_perf, 4)
        total_features = sum(r.get("feature_count", 0) for r in self.records)
        return {
            "session_name": self.session_name,
            "state": self.state,
            "crs_standard": "EPSG:7844",
            "start_time": self.start_wall_time,
            "total_duration_seconds": total_duration,
            "total_features_processed": total_features,
            "stages_completed": len(self.records),
            "stage_breakdown": self.records
        }

    def save_audit_log(self, filename: str = "telemetry_latest_v2.json") -> str:
        """Persists telemetry audit log to docs/audit_logs/."""
        os.makedirs(AUDIT_LOGS_DIR, exist_ok=True)
        out_path = os.path.join(AUDIT_LOGS_DIR, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(self.summarize(), f, indent=2)
        return out_path
