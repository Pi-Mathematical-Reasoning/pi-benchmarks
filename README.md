# pi-benchmarks

[![CI](https://github.com/Pi-Mathematical-Reasoning/pi-benchmarks/actions/workflows/ci.yml/badge.svg?event=pull_request)](https://github.com/Pi-Mathematical-Reasoning/pi-benchmarks/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/Pi-Mathematical-Reasoning/pi-benchmarks/blob/main/LICENSE)

The benchmark data for [Pi](https://github.com/Pi-Mathematical-Reasoning/pi),
mirrored in a private S3 bucket.

Pi pins every benchmark file by SHA-256 and fetches it from a public upstream.
This repository says which of those files are also kept in a bucket of Pi's
own, so the baseline can still be re-run if an upstream disappears. It holds
manifests and tooling. It holds no problem text.

## Status

**The bucket does not exist yet.** The project file and the manifests are
here; the bucket is created once [Jaws](https://github.com/Jaws-Platform/jaws)
registers the project and the owner runs its Bot apply. Until then Pi reads
every file from its upstream.

## What is mirrored

| Manifest | What it is | Size | Pi uses it as |
| --- | --- | --- | --- |
| [`math-500`](datasets/math-500.toml) | The 500 MATH test problems OpenAI selected for "Let's Verify Step by Step" | 447 KB | The scored benchmark |
| [`math-train-12k`](datasets/math-train-12k.toml) | The 12,000 MATH problems PRM800K trains on: MATH's training split and the test problems not in MATH-500 | 5.1 MB | The source of the 30 development problems |

Each file lives at `data/<name>/<sha256>/<file name>` in the bucket
`jaws-pi-benchmarks-problems`. A changed file has a new key, so nothing is
ever overwritten. `uv run pi-benchmarks check` prints every key.

## How it works

- **[`jaws.yaml`](jaws.yaml)** declares one dataset and nothing else. Jaws
  creates a private, versioned, kept-forever bucket, with no network and no
  instances.
- **A manifest** in `datasets/` names the upstream URL, pinned to a revision,
  and the file's SHA-256, size and license.
- **Nothing automated writes the bucket.** The owner imports each file with
  admin credentials, and only the owner's credentials can read it.

## Importing a file

Sign in to the production account first:

```sh
aws sso login --profile jaws-prod
export AWS_PROFILE=jaws-prod
```

Then import, and verify everything the bucket holds:

```sh
uv run pi-benchmarks import math-500
uv run pi-benchmarks import math-train-12k --from ~/Projects/Pi/data/math-dev-5bb914caa970.parquet
uv run pi-benchmarks verify
```

`import` fetches the upstream, or takes a local copy with `--from`, and checks
it against its manifest. It uploads only if the key is new, then reads the
object back and checks it again. Running it twice changes nothing.

## Adding a file

1. Add `datasets/<name>.toml` with the upstream URL pinned to a revision, the
   SHA-256, the size in bytes, and what the upstream says about its license.
2. Run `uv run pi-benchmarks check`, then open a pull request.
3. Once it has merged, import it as above.

## Development

The repository uses [uv](https://docs.astral.sh/uv/), which installs the
pinned Python (3.13) and the dependencies:

```sh
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

The tests reach neither AWS nor an upstream: a stand-in for the AWS CLI
(`tests/fake_aws.py`) answers on `PATH`.

## Contributing

Every change reaches `main` through a pull request with a Conventional
Commit title, and commits are a single line. [CONTRIBUTING.md](CONTRIBUTING.md)
has the setup and the rules; coding agents read [AGENTS.md](AGENTS.md).

## License

The code in this repository is [MIT](LICENSE). The benchmark files are not in
the repository and keep their own terms, as each manifest records.
