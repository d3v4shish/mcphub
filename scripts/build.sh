#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv sync --locked --group dev
uv run ruff check src tests
uv build
