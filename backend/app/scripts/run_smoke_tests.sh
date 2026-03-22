#!/usr/bin/env bash
set -euo pipefail

python -m app.demo.smoke_tests "$@"
