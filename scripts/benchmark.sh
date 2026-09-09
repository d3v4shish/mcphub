#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv sync --locked --group dev
uv run python examples/benchmark.py
