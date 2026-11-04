"""Assemble the Cloud Build context for a job in scratch/ (gitignored): job code, gate, manifest, regions, scoring.

  python tools/stage_job_context.py hydrosheds_ingest
Then: gcloud builds submit scratch/job_context/<job> --tag <image>
"""

import os
import shutil
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def stage(job: str) -> str:
    src = os.path.join(BASE, "jobs", job)
    if not os.path.isdir(src):
        raise SystemExit(f"unknown job {job!r}")
    dest = os.path.join(BASE, "scratch", "job_context", job)
    shutil.rmtree(dest, ignore_errors=True)
    os.makedirs(dest)
    for name in os.listdir(src):
        path = os.path.join(src, name)
        if os.path.isfile(path):
            shutil.copy2(path, dest)
    shutil.copy2(os.path.join(BASE, "src", "Ingestion_v2", "publish_gate.py"), dest)
    shutil.copy2(os.path.join(BASE, "tools", "build_parts_index.py"), dest)
    shutil.copy2(os.path.join(BASE, "config", "dataset_manifest_v2.json"), dest)
    shutil.copytree(os.path.join(BASE, "config", "regions"), os.path.join(dest, "regions"))
    scoring = os.path.join(BASE, "config", "scoring")
    if os.path.isdir(scoring):
        for name in os.listdir(scoring):
            shutil.copy2(os.path.join(scoring, name), dest)
    return dest


if __name__ == "__main__":
    print(stage(sys.argv[1]))
