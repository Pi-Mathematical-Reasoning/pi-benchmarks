"""The `pi-benchmarks` command, against a stand-in `aws` on PATH."""

import hashlib
import json

from pi_benchmarks.cli import main

CONTENT = b'{"problem": "What is $1+1$?", "answer": "2"}\n'
SHA = hashlib.sha256(CONTENT).hexdigest()
BUCKET = "jaws-pi-benchmarks-problems"


def project(tmp_path, sha256=SHA):
    """A checkout with a project file and one manifest; returns its root."""
    root = tmp_path / "checkout"
    (root / "datasets").mkdir(parents=True)
    (root / "jaws.yaml").write_text(
        "version: 1\nproject: pi-benchmarks\ncomponents:\n"
        f"  - kind: dataset\n    name: problems\n    bucket: {BUCKET}\n    prefix: data/\n"
    )
    (root / "datasets" / "sample.toml").write_text(
        'name = "sample"\n'
        'upstream = "https://example.com/sample/test.jsonl"\n'
        f'sha256 = "{sha256}"\n'
        f"size = {len(CONTENT)}\n"
        'license = "MIT"\n'
    )
    return root


def local_copy(tmp_path, content=CONTENT):
    path = tmp_path / "test.jsonl"
    path.write_bytes(content)
    return path


def test_check_lists_each_manifest_and_where_it_will_live(tmp_path, capsys):
    status = main(["check", "--root", str(project(tmp_path))])

    printed = capsys.readouterr().out
    assert status == 0
    assert f"s3://{BUCKET}/data/sample/{SHA}/test.jsonl" in printed


def test_check_fails_on_a_broken_manifest(tmp_path, capsys):
    status = main(["check", "--root", str(project(tmp_path, sha256="nope"))])

    assert status == 1
    assert "sha256" in capsys.readouterr().err


def test_import_uploads_a_checked_file_and_verify_then_finds_it(aws, tmp_path, capsys):
    root = str(project(tmp_path))

    imported = main(["import", "sample", "--from", str(local_copy(tmp_path)), "--root", root])
    verified = main(["verify", "--root", root])

    printed = capsys.readouterr().out
    assert (imported, verified) == (0, 0)
    assert "sample: imported" in printed
    assert "sample: ok" in printed
    assert (aws / BUCKET / "data" / "sample" / SHA / "test.jsonl").read_bytes() == CONTENT


def test_import_again_reports_the_file_already_present(aws, tmp_path, capsys):
    root = str(project(tmp_path))
    source = str(local_copy(tmp_path))
    main(["import", "sample", "--from", source, "--root", root])

    status = main(["import", "sample", "--from", source, "--root", root])

    assert status == 0
    assert "sample: already present" in capsys.readouterr().out


def test_import_refuses_a_file_that_does_not_match_and_uploads_nothing(aws, tmp_path, capsys):
    tampered = local_copy(tmp_path, CONTENT.replace(b'"2"', b'"3"'))

    status = main(["import", "sample", "--from", str(tampered), "--root", str(project(tmp_path))])

    assert status == 1
    assert "checksum" in capsys.readouterr().err
    assert not (aws / BUCKET).exists()


def test_import_names_a_manifest_that_does_not_exist(aws, tmp_path, capsys):
    status = main(["import", "absent", "--root", str(project(tmp_path))])

    assert status == 1
    assert "absent" in capsys.readouterr().err


def test_verify_fails_when_a_file_is_missing(aws, tmp_path, capsys):
    status = main(["verify", "--root", str(project(tmp_path))])

    assert status == 1
    assert "sample: missing" in capsys.readouterr().out


def test_commands_pass_the_profile_to_the_aws_cli(aws, tmp_path):
    main(["verify", "--profile", "jaws-prod", "--root", str(project(tmp_path))])

    call = json.loads((aws / "calls.jsonl").read_text().splitlines()[0])
    assert call[call.index("--profile") + 1] == "jaws-prod"


def test_expired_credentials_are_explained(aws, tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("FAKE_AWS_FAIL", "ExpiredToken")

    status = main(["verify", "--root", str(project(tmp_path))])

    assert status == 1
    assert "aws sso login" in capsys.readouterr().err
