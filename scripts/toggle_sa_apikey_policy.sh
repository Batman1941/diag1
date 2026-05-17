#!/usr/bin/env bash
set -euo pipefail

# Toggle org policy that controls Service Account API key creation.
# Constraint:
#   iam.managed.disableServiceAccountApiKeyCreation
#
# Modes:
#   allow -> enforce: false  (allow SA API key creation)
#   deny  -> enforce: true   (block SA API key creation)
#   reset -> remove project override (inherit from parent)

MODE="${1:-}"
PROJECT_ID="${2:-$(gcloud config get-value project 2>/dev/null || true)}"
CONSTRAINT="iam.managed.disableServiceAccountApiKeyCreation"

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/toggle_sa_apikey_policy.sh <allow|deny|reset> [PROJECT_ID]

Examples:
  ./scripts/toggle_sa_apikey_policy.sh allow your-gcp-project-id
  ./scripts/toggle_sa_apikey_policy.sh deny your-gcp-project-id
  ./scripts/toggle_sa_apikey_policy.sh reset your-gcp-project-id
USAGE
}

if [[ -z "$MODE" ]]; then
  usage
  exit 1
fi

if [[ -z "$PROJECT_ID" || "$PROJECT_ID" == "(unset)" ]]; then
  echo "No project provided and no active gcloud project found." >&2
  echo "Set it first: gcloud config set project <PROJECT_ID>" >&2
  exit 1
fi

PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
if [[ -z "$PROJECT_NUMBER" ]]; then
  echo "Cannot resolve project number for: $PROJECT_ID" >&2
  exit 1
fi

POLICY_NAME="projects/${PROJECT_NUMBER}/policies/${CONSTRAINT}"
TMP_FILE="/tmp/${PROJECT_ID//[^a-zA-Z0-9_-]/_}-sa-apikey-policy.yaml"

case "$MODE" in
  allow)
    printf 'name: %s\nspec:\n  rules:\n  - enforce: false\n' "$POLICY_NAME" > "$TMP_FILE"
    gcloud org-policies set-policy "$TMP_FILE"
    ;;
  deny)
    printf 'name: %s\nspec:\n  rules:\n  - enforce: true\n' "$POLICY_NAME" > "$TMP_FILE"
    gcloud org-policies set-policy "$TMP_FILE"
    ;;
  reset)
    gcloud org-policies reset "$CONSTRAINT" --project="$PROJECT_ID"
    ;;
  *)
    echo "Unknown mode: $MODE" >&2
    usage
    exit 1
    ;;
esac

echo
echo "Effective policy on project $PROJECT_ID:"
gcloud org-policies describe "$CONSTRAINT" --project="$PROJECT_ID" --effective --format='yaml(name,spec.rules)'
