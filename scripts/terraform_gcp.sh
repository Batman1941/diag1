#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/terraform_gcp.sh [--env <stage|dev>] <terraform-args...>

Examples:
  ./scripts/terraform_gcp.sh --env stage init
  ./scripts/terraform_gcp.sh --env stage apply -var-file=terraform.tfvars -auto-approve
  ./scripts/terraform_gcp.sh --env stage apply -var-file=terraform.tfvars -auto-approve -target=...

If --env is not provided, default is stage.
USAGE
}

ensure_env() {
  case "$1" in
    stage|dev) ;;
    *)
      echo "Unknown env '$1'. Allowed values: stage, dev." >&2
      usage
      exit 1
      ;;
  esac
}

ENV="stage"
if [[ ${1-} == "--env" ]]; then
  if [[ -z ${2-} ]]; then
    echo "Missing value for --env" >&2
    usage
    exit 1
  fi
  ENV="$2"
  shift 2
fi

ensure_env "$ENV"

if [[ ${1-} == "--help" || ${1-} == "-h" ]]; then
  usage
  exit 0
fi

if (( $# == 0 )); then
  usage
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$ROOT_DIR/terraform/$ENV"

if [[ ! -d "$TF_DIR" ]]; then
  echo "Unknown env '$ENV'. Directory '$TF_DIR' does not exist." >&2
  exit 1
fi

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud CLI is required in PATH." >&2
  exit 1
fi

ACTIVE_ACCOUNT="$(gcloud auth list --filter=status:ACTIVE --format='value(account)' | awk 'NF{print; exit}')"
if [[ -z "$ACTIVE_ACCOUNT" ]]; then
  echo "No active gcloud account. Run: gcloud auth login" >&2
  exit 1
fi

ACTIVE_PROJECT="$(gcloud config get-value project 2>/dev/null || true)"
if [[ -z "${ACTIVE_PROJECT}" || "$ACTIVE_PROJECT" == "(unset)" ]]; then
  echo "No active gcloud project. Set it first:"
  echo "  gcloud config set project <PROJECT_ID>"
  exit 1
fi

# Keep Terraform auth independent from stale application_default_credentials.
TOKEN="$(gcloud auth print-access-token)"
if [[ -z "$TOKEN" ]]; then
  echo "Cannot obtain gcloud access token. Run: gcloud auth login" >&2
  exit 1
fi

export GOOGLE_OAUTH_ACCESS_TOKEN="$TOKEN"
export GOOGLE_CLOUD_PROJECT="$ACTIVE_PROJECT"
export CLOUDSDK_CORE_PROJECT="$ACTIVE_PROJECT"

cd "$TF_DIR"

echo "Running in: $TF_DIR"
echo "Using account: $ACTIVE_ACCOUNT"
echo "Using project: $ACTIVE_PROJECT"
echo "Using GOOGLE_OAUTH_ACCESS_TOKEN length: ${#GOOGLE_OAUTH_ACCESS_TOKEN}"

exec terraform "$@"
