"""The `pi-benchmarks` command: check the manifests, import a file, verify the bucket."""

import argparse
import sys
import tempfile
from pathlib import Path

from pi_benchmarks.manifest import ManifestError, load_dataset, load_manifests
from pi_benchmarks.mirror import MirrorError, import_file, verify
from pi_benchmarks.s3 import AwsCli, S3Error


def main(argv: list[str] | None = None) -> int:
    options = _parser().parse_args(sys.argv[1:] if argv is None else argv)
    try:
        dataset = load_dataset(options.root / "jaws.yaml")
        manifests = load_manifests(options.root / "datasets", prefix=dataset.prefix)
    except (ManifestError, OSError) as error:
        return _fail(error)

    if options.command == "check":
        for manifest in manifests:
            print(f"{manifest.name}: s3://{dataset.bucket}/{manifest.key} ({manifest.size} bytes)")
        return 0

    bucket = AwsCli(profile=options.profile)
    with tempfile.TemporaryDirectory() as workdir:
        try:
            if options.command == "import":
                chosen = [m for m in manifests if m.name == options.name]
                if not chosen:
                    return _fail(f"no manifest named {options.name} in {options.root / 'datasets'}")
                outcome = import_file(
                    chosen[0], dataset.bucket, bucket, workdir=Path(workdir), source=options.source
                )
                print(f"{options.name}: {outcome}")
                return 0

            report = verify(manifests, dataset.bucket, bucket, workdir=Path(workdir))
        except (MirrorError, S3Error, OSError) as error:
            return _fail(error)

    for name, status in report.items():
        print(f"{name}: {status}")
    return 0 if all(status == "ok" for status in report.values()) else 1


def _fail(error: Exception | str) -> int:
    print(f"error: {error}", file=sys.stderr)
    return 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pi-benchmarks", description="Pi's benchmark data, mirrored in S3."
    )
    root = argparse.ArgumentParser(add_help=False)
    root.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="the checkout holding jaws.yaml and datasets/ (default: the current directory)",
    )
    aws = argparse.ArgumentParser(add_help=False)
    aws.add_argument("--profile", help="the AWS CLI profile (default: AWS_PROFILE)")

    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "check", parents=[root], help="check every manifest and print where each file lives"
    )
    importing = commands.add_parser(
        "import", parents=[root, aws], help="put one file in the bucket, checked before and after"
    )
    importing.add_argument("name", help="the manifest's name")
    importing.add_argument(
        "--from",
        dest="source",
        type=Path,
        help="a local copy to import instead of fetching the upstream",
    )
    commands.add_parser(
        "verify", parents=[root, aws], help="check every manifest's file as the bucket holds it"
    )
    return parser
