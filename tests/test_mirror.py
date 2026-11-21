"""Importing a file into the bucket and verifying what is there."""

import hashlib

import pytest

from pi_benchmarks.manifest import Manifest
from pi_benchmarks.mirror import MirrorError, import_file, verify

CONTENT = b'{"problem": "What is $1+1$?", "answer": "2"}\n'
SHA = hashlib.sha256(CONTENT).hexdigest()
BUCKET = "jaws-pi-benchmarks-problems"


SIZE = len(CONTENT)


def manifest(sha256=SHA, size=SIZE):
    return Manifest(
        name="sample",
        upstream="https://example.com/sample/test.jsonl",
        sha256=sha256,
        size=size,
        license="MIT",
        key=f"data/sample/{sha256}/test.jsonl",
    )


class FakeBucket:
    """An in-memory bucket that refuses to replace a key, as the import asks S3 to."""

    def __init__(self, objects=None):
        self.objects = dict(objects or {})
        self.puts = []

    def put_new(self, bucket, key, path):
        self.puts.append((bucket, key))
        if key in self.objects:
            return False
        self.objects[key] = path.read_bytes()
        return True

    def get(self, bucket, key, destination):
        if key not in self.objects:
            return False
        destination.write_bytes(self.objects[key])
        return True


def upstream_returning(content):
    calls = []

    def fetch(url, destination):
        calls.append(url)
        destination.write_bytes(content)

    fetch.calls = calls
    return fetch


def test_imports_a_file_from_its_upstream_and_reads_it_back(tmp_path):
    bucket = FakeBucket()
    fetch = upstream_returning(CONTENT)

    outcome = import_file(manifest(), BUCKET, bucket, fetch=fetch, workdir=tmp_path)

    assert outcome == "imported"
    assert bucket.objects == {f"data/sample/{SHA}/test.jsonl": CONTENT}
    assert fetch.calls == ["https://example.com/sample/test.jsonl"]


def test_imports_a_local_copy_instead_of_fetching(tmp_path):
    local = tmp_path / "copy.jsonl"
    local.write_bytes(CONTENT)
    bucket = FakeBucket()
    fetch = upstream_returning(b"never used")

    import_file(manifest(), BUCKET, bucket, fetch=fetch, workdir=tmp_path, source=local)

    assert fetch.calls == []
    assert bucket.objects[manifest().key] == CONTENT


def test_refuses_a_file_that_does_not_match_its_manifest_and_uploads_nothing(tmp_path):
    bucket = FakeBucket()

    # The same length, so only the checksum can tell.
    tampered = CONTENT.replace(b'"2"', b'"3"')

    with pytest.raises(MirrorError, match="checksum"):
        import_file(
            manifest(), BUCKET, bucket, fetch=upstream_returning(tampered), workdir=tmp_path
        )

    assert bucket.puts == []


def test_refuses_a_file_of_the_wrong_size_even_when_its_checksum_is_pinned_wrongly(tmp_path):
    with pytest.raises(MirrorError, match="size"):
        import_file(
            manifest(size=len(CONTENT) + 1),
            BUCKET,
            FakeBucket(),
            fetch=upstream_returning(CONTENT),
            workdir=tmp_path,
        )


def test_importing_again_changes_nothing_and_checks_what_is_there(tmp_path):
    bucket = FakeBucket({manifest().key: CONTENT})

    outcome = import_file(
        manifest(), BUCKET, bucket, fetch=upstream_returning(CONTENT), workdir=tmp_path
    )

    assert outcome == "already present"
    assert bucket.objects == {manifest().key: CONTENT}


def test_a_key_already_holding_other_bytes_is_an_error_not_an_overwrite(tmp_path):
    bucket = FakeBucket({manifest().key: b"something else"})

    with pytest.raises(MirrorError, match="does not match"):
        import_file(manifest(), BUCKET, bucket, fetch=upstream_returning(CONTENT), workdir=tmp_path)

    assert bucket.objects[manifest().key] == b"something else"


def test_verify_reports_each_file_as_it_stands_in_the_bucket(tmp_path):
    good = manifest()
    missing = Manifest(**{**vars(good), "name": "gone", "key": "data/gone/x/test.jsonl"})
    damaged = Manifest(**{**vars(good), "name": "bad", "key": "data/bad/x/test.jsonl"})
    bucket = FakeBucket({good.key: CONTENT, damaged.key: b"damaged"})

    report = verify([good, missing, damaged], BUCKET, bucket, workdir=tmp_path)

    assert report == {"sample": "ok", "gone": "missing", "bad": "does not match its manifest"}
