"""
JSON file-based versioning storage for specifications.
Structure: outputs/{trace_id}/v{n}.json + metadata.json
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./outputs")


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def save_spec(spec: dict, parent_trace_id: Optional[str] = None,
              refinement_instructions: Optional[str] = None) -> tuple[str, int]:
    """
    Save a spec to disk.
    Returns (trace_id, version).
    """
    if parent_trace_id:
        trace_id = parent_trace_id
        base_dir = os.path.join(OUTPUT_DIR, trace_id)
        _ensure_dir(base_dir)

        meta_path = os.path.join(base_dir, "metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                meta = json.load(f)
            version = meta.get("latest_version", 0) + 1
        else:
            version = 1
    else:
        trace_id = str(uuid.uuid4())
        base_dir = os.path.join(OUTPUT_DIR, trace_id)
        _ensure_dir(base_dir)
        version = 1

    # Update spec metadata
    spec["trace_id"] = trace_id
    spec["version"] = version
    spec["timestamp"] = datetime.now(timezone.utc).isoformat()

    # Save version file
    version_path = os.path.join(base_dir, f"v{version}.json")
    with open(version_path, "w") as f:
        json.dump(spec, f, indent=2)

    # Save/update metadata
    meta = {
        "trace_id": trace_id,
        "latest_version": version,
        "created_at": spec["timestamp"] if version == 1 else _get_existing_created_at(base_dir, trace_id),
        "updated_at": spec["timestamp"],
        "versions": _build_version_list(base_dir, version, refinement_instructions)
    }
    meta_path = os.path.join(base_dir, "metadata.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    return trace_id, version


def get_spec(trace_id: str, version: Optional[int] = None) -> Optional[dict]:
    """Get a specific version of a spec (latest if version is None)."""
    base_dir = os.path.join(OUTPUT_DIR, trace_id)
    meta_path = os.path.join(base_dir, "metadata.json")

    if not os.path.exists(meta_path):
        return None

    with open(meta_path, "r") as f:
        meta = json.load(f)

    if version is None:
        version = meta.get("latest_version", 1)

    version_path = os.path.join(base_dir, f"v{version}.json")
    if not os.path.exists(version_path):
        return None

    with open(version_path, "r") as f:
        return json.load(f)


def get_history(trace_id: str) -> Optional[dict]:
    """Get version history for a trace_id."""
    base_dir = os.path.join(OUTPUT_DIR, trace_id)
    meta_path = os.path.join(base_dir, "metadata.json")

    if not os.path.exists(meta_path):
        return None

    with open(meta_path, "r") as f:
        return json.load(f)


def _get_existing_created_at(base_dir: str, trace_id: str) -> str:
    meta_path = os.path.join(base_dir, "metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            meta = json.load(f)
        return meta.get("created_at", datetime.now(timezone.utc).isoformat())
    return datetime.now(timezone.utc).isoformat()


def _build_version_list(base_dir: str, latest_version: int,
                        refinement_instructions: Optional[str] = None) -> list:
    versions = []
    for v in range(1, latest_version + 1):
        vpath = os.path.join(base_dir, f"v{v}.json")
        if os.path.exists(vpath):
            with open(vpath, "r") as f:
                spec = json.load(f)
            entry = {
                "version": v,
                "timestamp": spec.get("timestamp", ""),
                "refinement_instructions": refinement_instructions if v == latest_version and v > 1 else None,
                "spec_summary": {
                    "module_count": len(spec.get("modules", [])),
                    "story_count": len(spec.get("user_stories", [])),
                    "endpoint_count": len(spec.get("api_endpoints", [])),
                    "table_count": len(spec.get("db_schema", [])),
                    "question_count": len(spec.get("open_questions", [])),
                }
            }
            versions.append(entry)
    return versions
