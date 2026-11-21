"""Manifests: one per mirrored file, saying where it came from and where it lives."""

from pathlib import Path

import pytest

from pi_benchmarks.manifest import Dataset, Manifest, ManifestError, load_dataset, load_manifests

ROOT = Path(__file__).parent.parent
SHA = "35dc41080a3680858b27fa7e0533d2d547825316fc5dafe5d316f4ccc5a06132"

VALID = f"""
name = "math-500"
upstream = "https://example.com/datasets/MATH-500/resolve/abc/test.jsonl"
sha256 = "{SHA}"
size = 446564
license = "MIT"
"""


def write(directory, name, text):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(text)
    return path


def test_reads_a_manifest_and_places_the_file_under_its_name_and_checksum(tmp_path):
    write(tmp_path, "math-500.toml", VALID)

    (manifest,) = load_manifests(tmp_path, prefix="data/")

    assert manifest == Manifest(
        name="math-500",
        upstream="https://example.com/datasets/MATH-500/resolve/abc/test.jsonl",
        sha256=SHA,
        size=446564,
        license="MIT",
        key=f"data/math-500/{SHA}/test.jsonl",
    )


def test_the_file_name_must_match_the_name_inside(tmp_path):
    write(tmp_path, "math500.toml", VALID)

    with pytest.raises(ManifestError, match="math500.toml"):
        load_manifests(tmp_path, prefix="data/")


@pytest.mark.parametrize(
    ("change", "complaint"),
    [
        ((f'"{SHA}"', '"35DC41"'), "sha256"),
        (("size = 446564", "size = 0"), "size"),
        (("size = 446564", 'size = "big"'), "size"),
        (('license = "MIT"\n', ""), "license"),
        (("https://example.com", "http://example.com"), "upstream"),
        (('name = "math-500"', 'name = "Math 500"'), "name"),
    ],
)
def test_refuses_a_manifest_with_a_bad_field(tmp_path, change, complaint):
    old, new = change
    name = "Math 500.toml" if "Math 500" in new else "math-500.toml"
    write(tmp_path, name, VALID.replace(old, new))

    with pytest.raises(ManifestError, match=complaint):
        load_manifests(tmp_path, prefix="data/")


def test_refuses_a_setting_it_does_not_know(tmp_path):
    write(tmp_path, "math-500.toml", VALID + 'imported = "2026-11-21"\n')

    with pytest.raises(ManifestError, match="imported"):
        load_manifests(tmp_path, prefix="data/")


def test_refuses_two_manifests_for_the_same_file(tmp_path):
    write(tmp_path, "math-500.toml", VALID)
    write(tmp_path, "copy.toml", VALID.replace('name = "math-500"', 'name = "copy"'))

    with pytest.raises(ManifestError, match="same file"):
        load_manifests(tmp_path, prefix="data/")


def test_reads_the_dataset_bucket_and_prefix_from_the_project_file(tmp_path):
    project = write(
        tmp_path,
        "jaws.yaml",
        "version: 1\nproject: pi-benchmarks\ncomponents:\n"
        "  - kind: dataset\n    name: problems\n    bucket: jaws-pi-benchmarks-problems\n"
        "    prefix: data/\n",
    )

    assert load_dataset(project) == Dataset(bucket="jaws-pi-benchmarks-problems", prefix="data/")


def test_refuses_a_project_file_without_exactly_one_dataset(tmp_path):
    project = write(tmp_path, "jaws.yaml", "version: 1\ncomponents: []\n")

    with pytest.raises(ManifestError, match="one dataset"):
        load_dataset(project)


def test_the_committed_manifests_and_project_file_are_valid():
    dataset = load_dataset(ROOT / "jaws.yaml")

    manifests = load_manifests(ROOT / "datasets", prefix=dataset.prefix)

    assert dataset.bucket == "jaws-pi-benchmarks-problems"
    assert {manifest.name for manifest in manifests} == {"math-500", "math-train-12k"}
    assert all(manifest.key.startswith("data/") for manifest in manifests)
