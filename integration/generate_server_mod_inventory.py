#!/usr/bin/env python3
"""Derive the trusted ATMons mod-JAR ledger from the exact server archive."""

from __future__ import annotations

import argparse
import hashlib
import os
import tempfile
import zipfile
from pathlib import Path


SERVER_ARCHIVE_SHA256 = "de112ed8d79b3ff027e399a5108b706f6a2db3be74b15d0db6f6b9d6ac268e6c"
SERVER_ARCHIVE_SIZE = 1_055_896_389
SERVER_MOD_COUNT = 375


class InventoryError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def build_rows(archive: Path, expected_count: int = SERVER_MOD_COUNT) -> list[str]:
    rows: dict[str, str] = {}
    try:
        with zipfile.ZipFile(archive) as source:
            for info in source.infolist():
                if not info.filename.startswith("mods/") or not info.filename.endswith(".jar"):
                    continue
                name = info.filename.removeprefix("mods/")
                if not name or Path(name).name != name or name in rows or info.file_size < 1:
                    raise InventoryError(f"invalid/duplicate server mod entry: {info.filename}")
                digest = hashlib.sha256()
                with source.open(info) as handle:
                    while chunk := handle.read(1024 * 1024):
                        digest.update(chunk)
                rows[name] = f"{name}\t{info.file_size}\t{digest.hexdigest()}"
    except (OSError, zipfile.BadZipFile) as exc:
        raise InventoryError(f"cannot read server archive {archive}: {exc}") from exc
    if len(rows) != expected_count:
        raise InventoryError(
            f"server archive contains {len(rows)} mod JARs, expected {expected_count}"
        )
    return [rows[name] for name in sorted(rows)]


def render(rows: list[str]) -> str:
    return (
        "# schema=bluemap-atmons-server-mod-inventory-v1\n"
        f"# serverArchiveSizeBytes={SERVER_ARCHIVE_SIZE}\n"
        f"# serverArchiveSha256={SERVER_ARCHIVE_SHA256}\n"
        + "\n".join(rows)
        + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    archive = args.archive.resolve()
    output = args.output.resolve()
    if not archive.is_file() or archive.stat().st_size != SERVER_ARCHIVE_SIZE:
        parser.error("server archive size does not match ATMons 1.2.0")
    if sha256(archive) != SERVER_ARCHIVE_SHA256:
        parser.error("server archive SHA-256 does not match ATMons 1.2.0")
    if output.exists():
        parser.error(f"refusing to replace existing output: {output}")
    content = render(build_rows(archive))
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"{sha256(output)}  {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
