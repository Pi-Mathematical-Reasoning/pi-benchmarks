# Contributing

`pi-benchmarks` keeps the manifests and tooling for the benchmark data that
[Pi](https://github.com/Pi-Mathematical-Reasoning/pi) mirrors in a private S3
bucket. [README.md](README.md) says what exists so far. Coding agents should
read [AGENTS.md](AGENTS.md).

## Local development setup

Requirements: [uv](https://docs.astral.sh/uv/), Node.js 24,
[pre-commit](https://pre-commit.com) and the GitHub CLI (`gh`). uv installs
the pinned Python itself.

```sh
git clone https://github.com/Pi-Mathematical-Reasoning/pi-benchmarks.git
cd pi-benchmarks
uv sync                                                           # Python and its dependencies
npm ci                                                            # commitlint
pre-commit install --hook-type commit-msg --hook-type pre-commit  # local hooks
```

The `commit-msg` hook runs commitlint locally. The `pre-commit` hooks run ruff
and a few file checks. They are conveniences only; **CI is the authoritative
check**.

Run the CI suite locally before opening a pull request:

```sh
scripts/check.sh
```

It needs no AWS credentials and no network, and neither does CI.

## Commits

Each commit message is a **single-line** Conventional Commit:

```
type(scope)?: subject
```

- At most 100 characters, with an imperative, lowercase subject and no
  trailing period.
- Allowed types: `feat`, `fix`, `docs`, `chore`, `refactor`, `ci`, `build`,
  `perf`, `style`, `test`, `revert`.
- Breaking changes are marked with `!`, for example `feat!: rename a field`.
- The **only** content allowed after the header is a blank line followed by
  `Co-authored-by: Name <email>` trailers. No body text. Details belong in the
  pull request description.

commitlint enforces this (`@commitlint/config-conventional` plus the local
`only-coauthor-trailers` rule in `tools/commitlint/`). The fixtures in
`tests/commitlint/` show accepted and rejected messages; CI checks them.

## Pull requests

- After the initial scaffold commit, **every change reaches `main` through a
  pull request**. Direct pushes are blocked.
- Merges are **squash or rebase only**. No merge commits; history is linear.
- The **title must be a valid Conventional Commit**, because a squash merge
  uses it as the commit message.
- Use the typed template for your change and fill in every section:

  ```sh
  gh pr create --template feat.md      # or fix.md, docs.md, chore.md, refactor.md, ci.md
  ```

  In the browser, append `?template=<type>.md` to the compare URL. `fix.md`
  also asks for Bug, Root cause and Reproduction.

CI runs these jobs on every pull request, and all of them are required on
`main`:

| Job | Checks |
|---|---|
| `commitlint` | Every commit in the range `base..head`, so rebase-merged commits are all checked |
| `pr-title` | The title is a Conventional Commit and passes the commit header rules |
| `commitlint-rules` | Unit tests for the local rule, and the fixture messages |
| `python` | `uv sync --locked`, `ruff check`, `ruff format --check` and `pytest` |

## Repository settings

`scripts/apply-repo-settings.sh` applies the settings through the GitHub API:

- Squash and rebase merges only; squash commits use the pull request title and
  a blank body. Head branches are deleted after merge.
- A ruleset on `main` requires a pull request, squash or rebase merges, every
  CI job as a status check and linear history, and blocks force pushes and
  deletion, with no bypass actors.

A new CI job is not required until it is added to the list in that script and
the script is run again.
