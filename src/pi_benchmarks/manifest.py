"""Manifests: one TOML file per mirrored file, in `datasets/`.

A manifest says where a file came from and what its bytes must be. The key it
lives at in the bucket is derived, never written: the dataset prefix, the
manifest's name, the file's SHA-256, then the upstream file name. A changed
file therefore has a new key, and no key is ever overwritten.
"""

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import yaml

_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_FIELDS = ("name", "upstream", "sha256", "size", "license")


class ManifestError(Exception):
    """A manifest or the project file cannot be used."""


@dataclass(frozen=True)
class Manifest:
    name: str
    upstream: str
    sha256: str
    size: int
    license: str
    key: str


@dataclass(frozen=True)
class Dataset:
    bucket: str
    prefix: str


def load_manifests(directory: Path, prefix: str) -> list[Manifest]:
    """Every manifest in `directory`, sorted by name."""
    manifests = [_load(path, prefix) for path in sorted(Path(directory).glob("*.toml"))]
    seen = {}
    for manifest in manifests:
        if manifest.sha256 in seen:
            raise ManifestError(
                f"{manifest.name} and {seen[manifest.sha256]} describe the same file"
            )
        seen[manifest.sha256] = manifest.name
    return manifests


def load_dataset(project_file: Path) -> Dataset:
    """The bucket and prefix of the one dataset the jaws project file declares."""
    project = yaml.safe_load(Path(project_file).read_text()) or {}
    datasets = [c for c in project.get("components") or [] if c.get("kind") == "dataset"]
    if len(datasets) != 1:
        raise ManifestError(f"{project_file} must declare exactly one dataset")
    return Dataset(bucket=datasets[0]["bucket"], prefix=datasets[0]["prefix"])


def _load(path: Path, prefix: str) -> Manifest:
    try:
        data = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as error:
        raise ManifestError(f"{path.name} is not valid TOML: {error}") from None

    unknown = sorted(set(data) - set(_FIELDS))
    if unknown:
        raise ManifestError(f"{path.name}: unknown setting {unknown[0]}")
    for field in _FIELDS:
        if field not in data:
            raise ManifestError(f"{path.name}: missing setting {field}")

    name, upstream, sha256, size = data["name"], data["upstream"], data["sha256"], data["size"]
    if not isinstance(name, str) or not _NAME.match(name):
        raise ManifestError(f"{path.name}: name must be kebab-case, not {name!r}")
    if path.stem != name:
        raise ManifestError(f"{path.name}: the file must be named {name}.toml")
    url = urlparse(upstream if isinstance(upstream, str) else "")
    if url.scheme != "https" or not url.netloc or not Path(url.path).name:
        raise ManifestError(f"{path.name}: upstream must be an https URL to a file")
    if not isinstance(sha256, str) or not _SHA256.match(sha256):
        raise ManifestError(f"{path.name}: sha256 must be 64 lowercase hex digits")
    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
        raise ManifestError(f"{path.name}: size must be a positive number of bytes")
    if not isinstance(data["license"], str) or not data["license"].strip():
        raise ManifestError(f"{path.name}: license must say what the upstream states")

    return Manifest(
        name=name,
        upstream=upstream,
        sha256=sha256,
        size=size,
        license=data["license"],
        key=f"{prefix}{name}/{sha256}/{Path(url.path).name}",
    )
