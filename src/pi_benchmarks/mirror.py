"""Putting a file in the bucket, and checking what the bucket holds.

Every byte is checked against its manifest twice: before the upload, and after
reading it back. The bucket refuses to replace an existing key, so importing
again only checks what is already there.
"""

import hashlib
import urllib.request
from pathlib import Path

from pi_benchmarks.manifest import Manifest


class MirrorError(Exception):
    """A file does not match its manifest, or the bucket holds something else."""


def fetch_url(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "pi-benchmarks"})
    with urllib.request.urlopen(request, timeout=120) as response:
        destination.write_bytes(response.read())


def import_file(
    manifest: Manifest,
    bucket_name: str,
    bucket,
    *,
    workdir: Path,
    fetch=fetch_url,
    source: Path | None = None,
) -> str:
    """Put one file in the bucket: "imported", or "already present" if it was there."""
    staged = Path(workdir) / f"{manifest.name}.upload"
    if source is None:
        fetch(manifest.upstream, staged)
    else:
        staged.write_bytes(Path(source).read_bytes())
    _check(manifest, staged, "the file to import")

    created = bucket.put_new(bucket_name, manifest.key, staged)

    status = _status(manifest, bucket_name, bucket, Path(workdir))
    if status != "ok":
        raise MirrorError(f"{manifest.name}: s3://{bucket_name}/{manifest.key} {status}")
    return "imported" if created else "already present"


def verify(manifests: list[Manifest], bucket_name: str, bucket, *, workdir: Path) -> dict:
    """Each manifest's file as it stands in the bucket: ok, missing, or not matching."""
    return {m.name: _status(m, bucket_name, bucket, Path(workdir)) for m in manifests}


def _status(manifest: Manifest, bucket_name: str, bucket, workdir: Path) -> str:
    copy = workdir / f"{manifest.name}.readback"
    if not bucket.get(bucket_name, manifest.key, copy):
        return "missing"
    try:
        _check(manifest, copy, "the stored copy")
    except MirrorError:
        return "does not match its manifest"
    return "ok"


def _check(manifest: Manifest, path: Path, what: str) -> None:
    content = path.read_bytes()
    if len(content) != manifest.size:
        raise MirrorError(
            f"{manifest.name}: {what} has size {len(content)}, the manifest says {manifest.size}"
        )
    found = hashlib.sha256(content).hexdigest()
    if found != manifest.sha256:
        raise MirrorError(
            f"{manifest.name}: {what} has checksum {found}, the manifest says {manifest.sha256}"
        )
