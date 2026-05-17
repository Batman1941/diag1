#!/usr/bin/env bash
# =============================================================================
# scripts/show_dns_records.sh
#
# Pokazuje, jaki rekord DNS A trzeba dodać, aby wystawić aplikację z Cloud Run LB.
#
# Użycie:
#   chmod +x scripts/show_dns_records.sh
#   ./scripts/show_dns_records.sh            # stage + dev
#   ./scripts/show_dns_records.sh stage      # tylko stage
#   ./scripts/show_dns_records.sh dev        # tylko dev
#
# Skrypt odczytuje:
# - domain  -> z terraform/<env>/terraform.tfvars (lub .example)
# - lb_ip   -> z `terraform output -raw lb_ip` dla katalogu env
# =============================================================================

set -euo pipefail

usage() {
  echo "Użycie: $0 [stage|dev|all]"
  echo "Przykład: $0 stage"
  exit 1
}

parse_tfvar() {
  local file="$1"
  local key="$2"

  awk -v key="$key" -F= '
    $1 ~ "^[[:space:]]*" key "[[:space:]]*$" {
      val=$0
      sub(/^[[:space:]]*[a-zA-Z0-9_]+[[:space:]]*=/, "", val)
      sub(/[[:space:]]*#.*$/, "", val)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", val)
      gsub(/^"/, "", val)
      gsub(/"$/, "", val)
      print val
      exit
    }
  ' "$file"
}

describe_env() {
  local env="$1"
  local tf_dir="terraform/${env}"
  local tf_file="$tf_dir/terraform.tfvars"
  local tf_file_example="$tf_dir/terraform.tfvars.example"
  local source_file=""
  local domain project_id ttl ip raw_output

  if [[ -f "$tf_file" ]]; then
    source_file="$tf_file"
  elif [[ -f "$tf_file_example" ]]; then
    source_file="$tf_file_example"
  else
    echo "❌ ${env}: brak pliku $tf_file ani $tf_file_example"
    return
  fi

  domain=$(parse_tfvar "$source_file" "domain" || true)
  project_id=$(parse_tfvar "$source_file" "project_id" || true)
  ttl=300

  if [[ -z "${domain}" ]]; then
    echo "❌ ${env}: nie znaleziono 'domain' w $source_file"
    return
  fi

  raw_output="$(cd "$tf_dir" && (terraform output -raw lb_ip 2>&1 || true))"
  ip="$(printf '%s\n' "$raw_output" | awk 'match($0,/^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$/){print; exit}')"
  source_msg="from state (terraform output)"

  if [[ -z "${ip}" ]] && [[ -n "${project_id}" ]] && command -v gcloud >/dev/null 2>&1; then
    if ! gcp_output="$(gcloud compute addresses list \
      --global \
      --project "$project_id" \
      --filter "name=(\"diag1-${env}-lb-ip\")" \
      --format "value(address)" 2>&1)"; then
      echo "⚠️  ${env}: nie mogę odczytać adresu LB z GCP (${gcp_output})"
      echo "    Najpierw sprawdź uprawnienia/aktywność projektu: ${project_id}"
      return
    fi
    ip="$(printf '%s\n' "$gcp_output" | awk 'match($0,/^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$/){print; exit}')"
    source_msg="from GCP Compute addresses"
  fi

  if [[ -z "${ip}" ]]; then
    echo "⚠️  ${env}: nie udało się pobrać lb_ip (brak apply/state lub output nie jest jeszcze dostępny)."
    echo "    Najpierw uruchom: cd ${tf_dir} && terraform init && terraform apply -var-file=terraform.tfvars"
    echo "    Po zastosowaniu: rekord A ${domain} -> <LB_IP>"
    return
  fi

  echo "✅ ${env}:"
  echo "   Dodaj rekord DNS (A):"
  echo "   Nazwa rekordu: ${domain}"
  echo "   Typ:          A"
  echo "   Wartość:      ${ip}"
  echo "   Źródło:       ${source_msg}"
  echo "   TTL:          ${ttl}"
  echo
}

ENV="${1:-all}"
case "$ENV" in
  stage|dev|all)
    ;;
  *)
    usage
    ;;
esac

if [[ "$ENV" == "all" ]]; then
  describe_env "dev"
  describe_env "stage"
else
  describe_env "$ENV"
fi
