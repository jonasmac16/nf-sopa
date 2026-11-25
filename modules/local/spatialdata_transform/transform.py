"""Generic executor for SpatialData transformation stages."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import spatialdata
from spatialdata import SpatialData

from operations import OperationError, get_operation


def _summarize_sdata(sdata: SpatialData) -> dict[str, list[str]]:
    """Return a JSON-serializable summary of the SpatialData object's element keys."""
    return {
        "images": sorted(sdata.images.keys()),
        "shapes": sorted(sdata.shapes.keys()),
        "points": sorted(sdata.points.keys()),
        "tables": sorted(sdata.tables.keys()),
    }


def _get_versions() -> dict[str, str | None]:
    """Collect relevant dependency versions."""
    try:
        sopa_version = _sopa_version()
    except Exception:
        sopa_version = None

    return {
        "spatialdata": spatialdata.__version__,
        "sopa": sopa_version,
    }


def _sopa_version() -> str:
    """Return the installed sopa CLI version string."""
    import subprocess

    result = subprocess.run(["sopa", "--version"], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def apply_operations(
    sdata: SpatialData,
    stage: str,
    operations: list[dict[str, Any]],
    meta: dict[str, Any],
) -> tuple[SpatialData, list[dict[str, Any]]]:
    """Apply an ordered list of operations to a SpatialData object.

    Args:
        sdata: the SpatialData object to transform.
        stage: current pipeline stage identifier.
        operations: list of operation configs with ``name`` and ``args`` keys.
        meta: sample metadata (must contain at least ``sample`` and ``technology``).

    Returns:
        Updated SpatialData object and a list of operation reports.

    Raises:
        OperationError: if validation or execution fails.
    """
    applied: list[dict[str, Any]] = []

    for index, op_config in enumerate(operations):
        name = op_config.get("name")
        args = op_config.get("args", {}) or {}

        if not isinstance(name, str):
            raise OperationError(f"Operation #{index} is missing a valid 'name' field.")
        if not isinstance(args, dict):
            raise OperationError(f"Operation '{name}' args must be a mapping, got {type(args).__name__}.")

        op_class = get_operation(name)
        op = op_class()
        context = {
            "name": name,
            "sample": meta.get("sample"),
            "technology": meta.get("technology"),
            "stage": stage,
            "args": args,
        }
        op.validate(context, sdata)
        sdata, report = op.apply(sdata, context)

        applied.append(
            {
                "name": name,
                "args": args,
                "affected_element_types": op.affected_element_types,
                "report": report,
            }
        )

    return sdata, applied


def run_stage(
    sdata_path: str,
    stage: str,
    operations: list[dict[str, Any]],
    meta: dict[str, Any],
    manifest_path: str,
) -> None:
    """Load a SpatialData object, apply operations, persist it, and write a manifest.

    The input ``sdata_path`` is expected to be a work-directory copy that this
    process is allowed to overwrite.
    """
    sdata_path_obj = Path(sdata_path)
    if not sdata_path_obj.exists():
        raise OperationError(f"SpatialData path does not exist: {sdata_path}")

    sdata = spatialdata.read_zarr(sdata_path)
    before_summary = _summarize_sdata(sdata)

    sdata, applied = apply_operations(sdata, stage, operations, meta)

    after_summary = _summarize_sdata(sdata)

    # Persist by writing to a temporary directory first, then atomically replacing
    # the existing work-directory copy. This avoids invalidating lazy element
    # references (e.g. Dask-backed points) by deleting the source before writing.
    tmp_path_obj = sdata_path_obj.parent / f"{sdata_path_obj.name}.tmp"
    if tmp_path_obj.exists():
        shutil.rmtree(tmp_path_obj)
    sdata.write(str(tmp_path_obj))

    shutil.rmtree(sdata_path_obj)
    tmp_path_obj.rename(sdata_path_obj)

    # Sanity check: the persisted object must be readable and have the expected summary.
    sdata_reopened = spatialdata.read_zarr(sdata_path)
    reopened_summary = _summarize_sdata(sdata_reopened)
    if reopened_summary != after_summary:
        raise OperationError(
            "Reopened SpatialData summary does not match the transformed summary. "
            f"Expected {after_summary}, got {reopened_summary}."
        )

    manifest = {
        "sample": meta.get("sample"),
        "stage": stage,
        "technology": meta.get("technology"),
        "operations": applied,
        "before_summary": before_summary,
        "after_summary": after_summary,
        "versions": _get_versions(),
    }

    manifest_path_obj = Path(manifest_path)
    manifest_path_obj.parent.mkdir(parents=True, exist_ok=True)
    manifest_path_obj.write_text(json.dumps(manifest, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Apply a SpatialData transformation stage.")
    parser.add_argument("--sdata-path", required=True, help="Path to the SpatialData .zarr directory.")
    parser.add_argument("--stage", required=True, help="Pipeline stage identifier.")
    parser.add_argument(
        "--operations",
        required=True,
        help="Path to a JSON file containing the ordered list of operation configs.",
    )
    parser.add_argument("--meta-file", required=True, help="Path to a JSON file containing sample metadata.")
    parser.add_argument("--manifest", required=True, help="Path where the stage manifest JSON will be written.")
    args = parser.parse_args(argv)

    operations = json.loads(Path(args.operations).read_text())
    if not isinstance(operations, list):
        raise OperationError("The operations JSON must contain a list.")

    meta = json.loads(Path(args.meta_file).read_text())
    if not isinstance(meta, dict):
        raise OperationError("The metadata JSON must contain an object.")

    run_stage(args.sdata_path, args.stage, operations, meta, args.manifest)


if __name__ == "__main__":
    main()
