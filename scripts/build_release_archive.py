#!/usr/bin/env python3
"""Build the deterministic public v1.3.0 payload, manifest, and checksum."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parent.parent
FIXED_TIMESTAMP = (2026, 8, 23, 12, 0, 0)
ARCHIVE_ROOT = "AI_urology_andrology-v1.3.0"
RELEASE_PATHS = (
    ".gitignore",
    ".zenodo.json",
    "CHANGELOG.md",
    "CITATION.cff",
    "README.md",
    "RELEASE_NOTES_v1.3.0.md",
    "REPRODUCIBILITY.md",
    "SUBMISSION_FILE_MAP.csv",
    "data/ai_only_include_audit.csv",
    "data/anchor_evidence_matrix.csv",
    "data/boundary_evidence.csv",
    "data/final_eligibility_verification.csv",
    "data/included_records.csv",
    "data/pubmed_search_strings.csv",
    "data/readiness_anchor_sources.csv",
    "data/readiness_anchor_summary_by_use_case.csv",
    "data/readiness_matrix.csv",
    "data/reporting_frameworks.csv",
    "data/review_burden_by_operational_analysis_group.csv",
    "data/screening_database.csv",
    "data/tiered_readiness_summary.csv",
    "data/top_journals.csv",
    "requirements.lock.txt",
    "requirements.txt",
    "scripts/ai_screening.py",
    "scripts/build_main_figures.py",
    "scripts/build_release_archive.py",
    "scripts/build_submission_file_map.py",
    "scripts/build_supplementary_figures.py",
    "scripts/csv_safety.py",
    "scripts/pubmed_harvest.py",
    "scripts/rebuild_all.py",
    "scripts/validate_release.py",
    "source_data/Figure1_PRISMA_flow_source_data.csv",
    "source_data/Figure2_readiness_map_source_data.csv",
    "source_data/Supplementary_Figure_S1_publication_trends_source_data.csv",
    "source_data/Supplementary_Figure_S2_review_burden_by_operational_analysis_group_source_data.csv",
    "source_data/review_burden_by_year.csv",
)


def approved_license_paths() -> tuple[str, ...]:
    """Return the exact profile-bound licence paths, or none before approval."""
    raw = os.environ.get("TAU_EXPECTED_LICENSE_PROFILE", "").strip()
    if not raw:
        return ()
    try:
        profile = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RuntimeError("TAU_EXPECTED_LICENSE_PROFILE is not valid JSON") from error
    license_files = profile.get("license_files") if isinstance(profile, dict) else None
    if not isinstance(license_files, dict) or not license_files:
        raise RuntimeError("Approved licence profile must declare a non-empty license_files mapping")
    normalized: list[str] = []
    for supplied in license_files:
        if not isinstance(supplied, str) or supplied != supplied.strip() or "\\" in supplied:
            raise RuntimeError(f"Invalid licence path in approved profile: {supplied!r}")
        relative = PurePosixPath(supplied)
        if (
            relative.is_absolute()
            or supplied != relative.as_posix()
            or not relative.parts
            or any(part in {"", ".", ".."} for part in relative.parts)
            or not relative.name.upper().startswith(("LICENSE", "COPYING"))
        ):
            raise RuntimeError(f"Unsafe or non-licence profile path: {supplied!r}")
        normalized.append(relative.as_posix())
    if len(set(normalized)) != len(normalized):
        raise RuntimeError("Approved licence profile contains colliding paths")
    return tuple(sorted(normalized))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def path_is_within(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
        return True
    except ValueError:
        return False


def safe_destination(requested: Path, protected_root: Path) -> Path:
    """Canonicalize a destination without following its final path component."""
    candidate = requested.expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    if candidate.is_symlink():
        raise RuntimeError(f"Destination must not be a symlink: {candidate}")
    if candidate.exists() and not candidate.is_file():
        raise RuntimeError(f"Destination must be a regular file path: {candidate}")
    canonical = candidate.parent.resolve() / candidate.name
    if path_is_within(canonical, protected_root.resolve()):
        raise RuntimeError(f"Destination must be outside the repository root: {canonical}")
    return canonical


def atomic_write_text(path: Path, text: str) -> None:
    """Replace a sidecar atomically without following a destination symlink."""
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def payload_tree_sha256(payloads: list[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    for relative_text, payload in payloads:
        relative = relative_text.encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def verify_archive(path: Path, payloads: list[tuple[str, bytes]]) -> None:
    expected_names = [f"{ARCHIVE_ROOT}/{relative}" for relative, _ in payloads]
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None or archive.namelist() != expected_names:
            raise RuntimeError("Archive CRC, entry set, or deterministic ordering failed")
        for (relative, payload), name in zip(payloads, expected_names):
            if archive.read(name) != payload:
                raise RuntimeError(f"Archive/source-snapshot mismatch: {relative}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Destination ZIP path")
    args = parser.parse_args()
    requested_output = args.output.expanduser()
    if requested_output.suffix.lower() != ".zip":
        raise RuntimeError("Release output must use a .zip filename")
    output = safe_destination(requested_output, ROOT)
    manifest_path = safe_destination(output.with_suffix(".manifest.json"), ROOT)
    checksum_path = safe_destination(output.with_suffix(output.suffix + ".sha256"), ROOT)
    protected_outputs = (output, manifest_path, checksum_path)
    if len(set(protected_outputs)) != len(protected_outputs):
        raise RuntimeError("Release archive and sidecar paths must be distinct")
    license_paths = approved_license_paths()
    release_contract = tuple(sorted((*RELEASE_PATHS, *license_paths)))
    paths = [ROOT / relative for relative in release_contract]
    missing = [path.relative_to(ROOT).as_posix() for path in paths if not path.is_file()]
    symlinks = [path.relative_to(ROOT).as_posix() for path in paths if path.is_symlink()]
    if missing or symlinks:
        raise RuntimeError(f"Invalid release contract: missing={missing}, symlinks={symlinks}")

    child_environment = os.environ.copy()
    child_environment["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_release.py"), "--require-figures"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        env=child_environment,
    )

    payloads = [
        (path.relative_to(ROOT).as_posix(), path.read_bytes())
        for path in paths
    ]
    file_records = [
        {
            "path": relative,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
        for relative, payload in payloads
    ]
    tree_sha256 = payload_tree_sha256(payloads)

    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.stem}.", suffix=".tmp", dir=output.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for relative, payload in payloads:
                archive_name = f"{ARCHIVE_ROOT}/{relative}"
                info = zipfile.ZipInfo(archive_name, date_time=FIXED_TIMESTAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(
                    info,
                    payload,
                    compress_type=zipfile.ZIP_DEFLATED,
                    compresslevel=9,
                )
        verify_archive(temporary, payloads)
        changed_sources = [
            relative
            for (relative, payload), path in zip(payloads, paths)
            if path.read_bytes() != payload
        ]
        if changed_sources:
            raise RuntimeError(f"Release sources changed during archive build: {changed_sources}")
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)

    verify_archive(output, payloads)

    manifest = {
        "archive": output.name,
        "archive_sha256": sha256(output),
        "archive_bytes": output.stat().st_size,
        "archive_root": ARCHIVE_ROOT,
        "file_count": len(payloads),
        "payload_tree_sha256": tree_sha256,
        "fixed_zip_timestamp": list(FIXED_TIMESTAMP),
        "network_operations_invoked_by_builder": False,
        "license_profile_supplied": bool(license_paths),
        "license_files_included": list(license_paths),
        "files": file_records,
    }
    atomic_write_text(
        manifest_path,
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
    )
    atomic_write_text(
        checksum_path,
        f"{manifest['archive_sha256']}  {output.name}\n",
    )
    changed_sources = [
        relative
        for (relative, payload), path in zip(payloads, paths)
        if path.read_bytes() != payload
    ]
    if changed_sources:
        raise RuntimeError(f"Release sources changed during sidecar writes: {changed_sources}")
    verify_archive(output, payloads)
    print(json.dumps({key: manifest[key] for key in ("archive", "archive_sha256", "archive_bytes", "file_count", "payload_tree_sha256", "network_operations_invoked_by_builder")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
