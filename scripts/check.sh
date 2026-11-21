#!/usr/bin/env bash
# Runs the CI suite locally: the Python lint, format check and tests, the
# commit-message tooling, and commitlint over this branch's commits. Run it
# before opening a pull request. Only the pull request title is left to CI.
#
#   scripts/check.sh
#
# Requires uv and node.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> uv sync --locked"
uv sync --locked

echo "==> ruff check"
uv run ruff check .

echo "==> ruff format --check"
uv run ruff format --check .

echo "==> pytest"
uv run pytest

echo
echo "==> commit-message tooling"
[[ -d node_modules ]] || npm ci
npm test

# The same range CI lints, when the branch has commits that main does not.
if git rev-parse --verify --quiet origin/main > /dev/null \
  && [[ -n "$(git rev-list origin/main..HEAD)" ]]; then
  echo
  echo "==> commitlint origin/main..HEAD"
  npx --no-install commitlint --from origin/main --to HEAD --verbose
fi

echo
echo "All checks passed."
