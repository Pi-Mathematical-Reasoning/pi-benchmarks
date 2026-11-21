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

**Nothing is mirrored yet.** The repository holds an empty Python package. The
project file, the manifests and the import tool come next.

## Development

The repository uses [uv](https://docs.astral.sh/uv/), which installs the
pinned Python (3.13) and the dependencies:

```sh
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

## Contributing

Every change reaches `main` through a pull request with a Conventional
Commit title, and commits are a single line. [CONTRIBUTING.md](CONTRIBUTING.md)
has the setup and the rules; coding agents read [AGENTS.md](AGENTS.md).

## License

[MIT](LICENSE)
