"""The AWS CLI boundary, against a stand-in `aws` on PATH."""

import json
import shutil

import pytest

from pi_benchmarks.s3 import AwsCli, S3Error

BUCKET = "jaws-pi-benchmarks-problems"
KEY = "data/sample/abc/test.jsonl"


def calls(store):
    return [json.loads(line) for line in (store / "calls.jsonl").read_text().splitlines()]


def a_file(tmp_path, content=b"payload"):
    path = tmp_path / "upload.jsonl"
    path.write_bytes(content)
    return path


def test_uploads_only_if_the_key_is_new_and_has_s3_check_the_bytes(aws, tmp_path):
    created = AwsCli().put_new(BUCKET, KEY, a_file(tmp_path))

    assert created is True
    (call,) = calls(aws)
    assert call[:2] == ["s3api", "put-object"]
    assert call[call.index("--if-none-match") + 1] == "*"
    assert call[call.index("--checksum-algorithm") + 1] == "SHA256"
    assert (aws / BUCKET / KEY).read_bytes() == b"payload"


def test_reports_a_key_that_already_exists_without_replacing_it(aws, tmp_path):
    AwsCli().put_new(BUCKET, KEY, a_file(tmp_path, b"first"))

    created = AwsCli().put_new(BUCKET, KEY, a_file(tmp_path, b"second"))

    assert created is False
    assert (aws / BUCKET / KEY).read_bytes() == b"first"


def test_downloads_an_object(aws, tmp_path):
    AwsCli().put_new(BUCKET, KEY, a_file(tmp_path))

    assert AwsCli().get(BUCKET, KEY, tmp_path / "copy") is True
    assert (tmp_path / "copy").read_bytes() == b"payload"


def test_reports_a_missing_object(aws, tmp_path):
    assert AwsCli().get(BUCKET, KEY, tmp_path / "copy") is False


def test_passes_the_profile_when_one_is_given(aws, tmp_path):
    AwsCli(profile="jaws-prod").get(BUCKET, KEY, tmp_path / "copy")

    (call,) = calls(aws)
    assert call[call.index("--profile") + 1] == "jaws-prod"


def test_says_to_sign_in_when_the_credentials_have_expired(aws, tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_AWS_FAIL", "ExpiredToken")

    with pytest.raises(S3Error, match="aws sso login"):
        AwsCli().get(BUCKET, KEY, tmp_path / "copy")


def test_passes_on_any_other_error(aws, tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_AWS_FAIL", "AccessDenied")

    with pytest.raises(S3Error, match="AccessDenied"):
        AwsCli().put_new(BUCKET, KEY, a_file(tmp_path))


def test_says_so_when_the_aws_cli_is_not_installed(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))

    with pytest.raises(S3Error, match="AWS CLI"):
        AwsCli().get(BUCKET, KEY, tmp_path / "copy")


@pytest.mark.skipif(shutil.which("aws") is None, reason="the real AWS CLI is not installed")
def test_the_real_aws_cli_accepts_the_upload_options():
    # The options exist in the installed CLI's own help, so a real upload will not
    # be refused for an unknown argument.
    import subprocess

    help_text = subprocess.run(
        ["aws", "s3api", "put-object", "help"], capture_output=True, text=True
    ).stdout
    assert "--if-none-match" in help_text
    assert "--checksum-algorithm" in help_text
