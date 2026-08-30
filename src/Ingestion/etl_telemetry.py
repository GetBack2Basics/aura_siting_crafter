#!/usr/bin/env python3
"""
AURA Siting Crafter — High-Resolution Spatial ETL Telemetry & Timing Logger (etl_telemetry.py)

Instruments spatial data ingestion, reprojections, buffering, and persistence operations.
Outputs structured JSON and Markdown audit logs for comparative performance analysis,
efficiency benchmarking, and publication in architectural articles and case studies.
"""

import os
import sys
import json
import time
import datetime
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
AUDIT_DIR = os.path.join(DOCS_DIR, "audit_logs")


class StageTimer:
    """Context manager for high-resolution timing of an individual ETL phase."""
    def __init__(self, stage_name: str, logger: "ETLTelemetryLogger"):
        self.stage_name = stage_name
        self.logger = logger
        self.start_time = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self.start_time
        self.logger.record_stage_timing(self.stage_name, elapsed)


class ETLTelemetryLogger:
    """
    Collects, aggregates, and outputs structured performance metrics and telemetry
    across all spatial dataset ingestion runs.
    """
    def __init__(self, run_id: Optional[str] = None):
        self.run_id = run_id or f"etl_run_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        self.start_timestamp_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.overall_start = time.perf_counter()
        self.dataset_records: Dict[str, Dict[str, Any]] = {}
        self.current_dataset: Optional[str] = None

    def start_dataset(self, dataset_key: str, dataset_name: str, portal: str, target_crs: str):
        """Begins tracking telemetry for a specific dataset."""
        self.current_dataset = dataset_key
        self.dataset_records[dataset_key] = {
            "dataset_key": dataset_key,
            "dataset_name": dataset_name,
            "portal": portal,
            "target_crs": target_crs,
            "stages": {},
            "metrics": {
                "feature_count_raw": 0,
                "feature_count_valid": 0,
                "throughput_features_per_sec": 0.0,
                "cache_hit_skipped": False,
                "etag_or_hash": None,
                "http_status_code": 200,
                "table_name": dataset_key,
                "storage_format": "havasu.iceberg",
            },
            "start_time": time.perf_counter(),
            "total_duration_s": 0.0,
            "status": "IN_PROGRESS",
            "notes": ""
        }

    def record_stage_timing(self, stage_name: str, duration_s: float):
        """Records the elapsed seconds for a named pipeline stage."""
        if self.current_dataset and self.current_dataset in self.dataset_records:
            self.dataset_records[self.current_dataset]["stages"][stage_name] = round(duration_s, 4)

    def time_stage(self, stage_name: str) -> StageTimer:
        """Returns a context manager for timing a stage."""
        return StageTimer(stage_name, self)

    def update_metrics(self, dataset_key: Optional[str] = None, **kwargs):
        """Updates metadata and counts for the active or specified dataset."""
        key = dataset_key or self.current_dataset
        if key and key in self.dataset_records:
            self.dataset_records[key]["metrics"].update(kwargs)

    def finish_dataset(self, dataset_key: Optional[str] = None, status: str = "SUCCESS", notes: str = ""):
        """Concludes tracking for a dataset and computes aggregate throughput."""
        key = dataset_key or self.current_dataset
        if key and key in self.dataset_records:
            rec = self.dataset_records[key]
            total_duration = time.perf_counter() - rec["start_time"]
            rec["total_duration_s"] = round(total_duration, 4)
            rec["status"] = status
            rec["notes"] = notes
            
            valid_cnt = rec["metrics"].get("feature_count_valid", 0)
            if total_duration > 0 and valid_cnt > 0:
                rec["metrics"]["throughput_features_per_sec"] = round(valid_cnt / total_duration, 2)

    def save_telemetry_report(self) -> Dict[str, str]:
        """
        Saves structured telemetry to JSON and Markdown audit logs in docs/audit_logs/.
        Returns paths to saved files.
        """
        os.makedirs(AUDIT_DIR, exist_ok=True)
        total_pipeline_time = round(time.perf_counter() - self.overall_start, 4)
        total_features = sum(r["metrics"].get("feature_count_valid", 0) for r in self.dataset_records.values())

        report_data = {
            "run_id": self.run_id,
            "timestamp_utc": self.start_timestamp_utc,
            "total_datasets_tracked": len(self.dataset_records),
            "total_features_processed": total_features,
            "total_pipeline_duration_s": total_pipeline_time,
            "avg_throughput_features_per_sec": round(total_features / total_pipeline_time, 2) if total_pipeline_time > 0 else 0.0,
            "datasets": self.dataset_records
        }

        # 1. Save JSON Log
        json_path = os.path.join(AUDIT_DIR, f"telemetry_{self.run_id}.json")
        latest_json = os.path.join(AUDIT_DIR, "telemetry_latest.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        with open(latest_json, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        # 2. Save Markdown Report for easy reading & blog publication
        md_path = os.path.join(AUDIT_DIR, f"telemetry_report_{self.run_id}.md")
        latest_md = os.path.join(AUDIT_DIR, "telemetry_report.md")
        md_content = self._generate_markdown_report(report_data)

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        with open(latest_md, "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"[etl_telemetry] Telemetry JSON persisted to: {latest_json}")
        print(f"[etl_telemetry] Telemetry Markdown persisted to: {latest_md}")
        return {"json_path": latest_json, "markdown_path": latest_md}

    def _generate_markdown_report(self, data: dict) -> str:
        """Formats the telemetry audit data into a GitHub markdown table report."""
        lines = [
            f"# Spatial ETL Performance & Telemetry Benchmark Report",
            f"",
            f"**Run ID:** `{data['run_id']}`  ",
            f"**Timestamp (UTC):** `{data['timestamp_utc']}`  ",
            f"**Total Datasets Ingested:** `{data['total_datasets_tracked']}`  ",
            f"**Total Geometries Processed:** `{data['total_features_processed']:,}`  ",
            f"**Total Pipeline Runtime:** `{data['total_pipeline_duration_s']} seconds` (~`{round(data['total_pipeline_duration_s'] / 60.0, 2)} minutes`)  ",
            f"**Average Ingestion Throughput:** `{data['avg_throughput_features_per_sec']} features/sec`  ",
            f"",
            f"---",
            f"",
            f"## 1. Dataset Execution Breakdown & Timing Matrix",
            f"",
            f"| Dataset Key | Portal / Source | Target CRS | Valid Features | Download (s) | Clean & Repair (s) | Projection (s) | Metric Buffer (s) | Storage Write (s) | Total (s) | Throughput (feat/s) | Status |",
            f"| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
        ]

        for k, v in data["datasets"].items():
            stages = v.get("stages", {})
            m = v.get("metrics", {})
            d_time = stages.get("1_download_harvest", 0.0)
            c_time = stages.get("2_clean_and_repair", 0.0)
            p_time = stages.get("3_crs_projection", 0.0)
            b_time = stages.get("4_metric_buffer", 0.0)
            w_time = stages.get("5_storage_write", 0.0)
            tot = v.get("total_duration_s", 0.0)
            throughput = m.get("throughput_features_per_sec", 0.0)
            feat_cnt = m.get("feature_count_valid", 0)
            status = v.get("status", "UNKNOWN")

            lines.append(
                f"| `{k}` | {v.get('portal', 'N/A')} | `{v.get('target_crs', 'EPSG:7844')}` | {feat_cnt:,} | {d_time:.2f} | {c_time:.2f} | {p_time:.2f} | {b_time:.2f} | {w_time:.2f} | **{tot:.2f}** | {throughput:.1f} | `{status}` |"
            )

        lines.extend([
            f"",
            f"---",
            f"",
            f"## 2. Architectural Efficiency & Optimization Notes",
            f"",
            f"- **Phase 1 Separation:** All authoritative vector layers were harvested, cleaned, and standardized to `EPSG:7844` prior to performing any multi-layer topological operations.",
            f"- **Metric Buffering:** Buffers were dynamically projected to `EPSG:3112` (Geoscience Australia National Albers) for exact meter calculations and persisted back to `EPSG:7844`.",
            f"- **Compute Cost Guardrail:** Sessions terminated gracefully with `sedona.stop()` to eliminate idle cluster charges.",
            f"- **Future State Comparison:** This benchmark log provides the baseline for measuring cloud savings when enabling Delta Partition processing and ETag cache skipping."
        ])

        return "\n".join(lines)
