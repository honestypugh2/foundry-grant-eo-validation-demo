#!/usr/bin/env bash
# Deploy the grant_compliance_host function app to Azure.
#
# Copies the shared `src/agents` package into the function app directory so
# Azure Functions can resolve `from agents.xxx import …` imports at runtime,
# then publishes with remote build and removes the temporary copy.
#
# Usage:
#   ./scripts/deploy_compliance_function.sh [function-app-name]
#
# Default function app name: func-compliance-grant-eo-dev

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FUNC_DIR="${REPO_ROOT}/src/functions/grant_compliance_host"
AGENTS_SRC="${REPO_ROOT}/src/agents"
AGENTS_DST="${FUNC_DIR}/agents"
FUNC_APP_NAME="${1:-func-compliance-grant-eo-dev}"

echo "==> Copying agents package into function app directory..."
rm -rf "${AGENTS_DST}"
cp -r "${AGENTS_SRC}" "${AGENTS_DST}"
# Remove __pycache__ dirs from the copy
find "${AGENTS_DST}" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true

echo "==> Publishing ${FUNC_APP_NAME}..."
cd "${FUNC_DIR}"
func azure functionapp publish "${FUNC_APP_NAME}" --python

echo "==> Cleaning up temporary agents copy..."
rm -rf "${AGENTS_DST}"

echo "==> Done."
