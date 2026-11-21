# Rules for coding agents

This file restates the repository conventions for coding agents. The
human-facing version, with setup details, is
[CONTRIBUTING.md](CONTRIBUTING.md). What the repository is for is in
[README.md](README.md).

## Non-negotiable

- **Never push to `main`.** Every change reaches `main` through a pull request.
  Direct pushes are blocked by a branch ruleset; do not try to work around it.
- **Open pull requests with a typed template and fill in every section:**

  ```sh
  gh pr create --template <type>.md   # feat.md | fix.md | docs.md | chore.md | refactor.md | ci.md
  ```

  Leaving a section empty or deleting it is not acceptable. `fix.md` also
  needs Bug, Root cause and Reproduction.
- **Pull request titles are Conventional Commits** (`type(scope)?: subject`,
  100 characters at most). The title becomes the squash-merge commit message.
- **Commits are a single line**: `type(scope)?: subject`, at most 100
  characters. After that line, only a blank line and
  `Co-authored-by: Name <email>` trailers are allowed. No body text; details
  go in the pull request description. Allowed types: `feat`, `fix`, `docs`,
  `chore`, `refactor`, `ci`, `build`, `perf`, `style`, `test`, `revert`.
  Breaking changes use `!` (`feat!: ...`).
- **Spell the trailer `Co-authored-by:` exactly.** The check is
  case-sensitive, so `Co-Authored-By:` fails it.
- **Merges are squash or rebase only.** History stays linear.
- **Releases are made by merging the Release Please pull request**, which is
  authored by `pi-release-bot[bot]`. Do not create tags or releases by hand,
  and do not edit `CHANGELOG.md` or `version.txt`.
- **Run the checks before opening a pull request:**

  ```sh
  scripts/check.sh
  ```

## Working in this repo

- **No problem text, ever.** This repository is public and the benchmark data
  is not ours to redistribute. Never commit a benchmark file, an excerpt of
  one, or a model's reply to a benchmark problem.
- **Python goes through uv.** The package is `src/pi_benchmarks/` and its
  tests are `tests/`. Add a dependency with `uv add` and commit `uv.lock`; CI
  installs with `uv sync --locked`, so a stale lock fails.
- **CI has no AWS credentials.** A test must pass without reaching S3 or an
  upstream.

## Things that need the owner

Repository settings and secrets, and anything that touches AWS. List them in
the pull request instead of attempting them.
