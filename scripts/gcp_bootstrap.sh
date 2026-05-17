#!/usr/bin/env bash
# =============================================================================
# scripts/gcp_bootstrap.sh
#
# Uruchom RAZ przed pierwszym `terraform apply`, aby:
#   1. Połączyć projekt z kontem rozliczeniowym
#   2. Włączyć wymagane API
#   3. Utworzyć bucket GCS na stan Terraform
#
# Wymagania:
#   - gcloud CLI zainstalowane i zalogowane (gcloud auth login)
#   - Projekt GCP już musi istnieć (utwórz w konsoli lub przez gcloud)
#
# Użycie:
#   chmod +x scripts/gcp_bootstrap.sh
#   ./scripts/gcp_bootstrap.sh <PROJECT_ID> <BILLING_ACCOUNT_ID>
#
# Przykład:
#   ./scripts/gcp_bootstrap.sh diag1-thesis-2026 0X0X0X-0X0X0X-0X0X0X
#
# Aby znaleźć ID konta rozliczeniowego:
#   gcloud billing accounts list
# =============================================================================

set -euo pipefail

# ── Kolory do logów ──────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'
BOLD='\033[1m'; RESET='\033[0m'

log()  { echo -e "${BLUE}>>>  $*${RESET}"; }
ok()   { echo -e "${GREEN}[OK] $*${RESET}"; }
warn() { echo -e "${YELLOW}[!]  $*${RESET}"; }
err()  { echo -e "${RED}[ERR] $*${RESET}" >&2; exit 1; }

usage() {
  echo -e "${BOLD}Użycie:${RESET} $0 <PROJECT_ID> <BILLING_ACCOUNT_ID> [REGION]"
  echo ""
  echo "  PROJECT_ID          – ID projektu GCP (np. diag1-thesis-2026)"
  echo "  BILLING_ACCOUNT_ID  – ID konta rozliczeniowego GCP"
  echo "  REGION              – Region GCP (domyślnie: europe-west4)"
  echo ""
  echo "Aby znaleźć BILLING_ACCOUNT_ID:"
  echo "  gcloud billing accounts list"
  echo ""
  echo "Aby znaleźć lub utworzyć projekt GCP:"
  echo "  gcloud projects list"
  echo "  gcloud projects create <PROJECT_ID>"
  exit 1
}

[[ $# -lt 2 ]] && usage

PROJECT_ID="$1"
BILLING_ACCOUNT="$2"
REGION="${3:-europe-west4}"
STATE_BUCKET="${PROJECT_ID}-tfstate"

echo ""
echo -e "${BOLD}══════════════════════════════════════════════${RESET}"
echo -e "${BOLD}   Diag1 – Bootstrap projektu GCP            ${RESET}"
echo -e "${BOLD}══════════════════════════════════════════════${RESET}"
echo ""
echo -e "  Projekt GCP:       ${BOLD}${PROJECT_ID}${RESET}"
echo -e "  Konto rozlicz.:    ${BOLD}${BILLING_ACCOUNT}${RESET}"
echo -e "  Region:            ${BOLD}${REGION}${RESET}"
echo -e "  Bucket TF state:   ${BOLD}gs://${STATE_BUCKET}${RESET}"
echo ""
read -rp "Czy kontynuować? [y/N] " confirm
[[ "$confirm" =~ ^[yY]$ ]] || { echo "Anulowano."; exit 0; }
echo ""

# ── 1. Uwierzytelnienie ──────────────────────────────────────────────────────
log "Sprawdzanie uwierzytelnienia gcloud..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
  warn "Nie jesteś zalogowany. Uruchamiam gcloud auth login..."
  gcloud auth login
fi
ok "Zalogowany jako: $(gcloud auth list --filter=status:ACTIVE --format='value(account)' | head -1)"

# ── 2. Ustawienie projektu ────────────────────────────────────────────────────
log "Ustawianie aktywnego projektu: ${PROJECT_ID}"
gcloud config set project "${PROJECT_ID}"
ok "Projekt ustawiony."

# ── 3. Powiązanie konta rozliczeniowego ──────────────────────────────────────
log "Powiązywanie konta rozliczeniowego..."
if gcloud billing projects describe "${PROJECT_ID}" \
    --format="value(billingEnabled)" 2>/dev/null | grep -q "True"; then
  warn "Billing już jest włączony dla projektu, pomijam."
else
  gcloud billing projects link "${PROJECT_ID}" \
    --billing-account="${BILLING_ACCOUNT}"
  ok "Billing powiązany."
fi

# ── 4. Włączenie wymaganych API ──────────────────────────────────────────────
log "Włączanie wymaganych API Google Cloud..."

APIS=(
  "cloudresourcemanager.googleapis.com"
  "iam.googleapis.com"
  "storage.googleapis.com"
  "run.googleapis.com"
  "sqladmin.googleapis.com"
  "artifactregistry.googleapis.com"
  "compute.googleapis.com"
  "aiplatform.googleapis.com"
)

gcloud services enable "${APIS[@]}"
ok "Wszystkie API włączone."

# ── 5. Bucket GCS na stan Terraform ─────────────────────────────────────────
log "Tworzenie bucketu GCS na stan Terraform: gs://${STATE_BUCKET}"

if gsutil ls "gs://${STATE_BUCKET}" &>/dev/null; then
  warn "Bucket już istnieje: gs://${STATE_BUCKET}, pomijam tworzenie."
else
  gsutil mb -l EU -p "${PROJECT_ID}" "gs://${STATE_BUCKET}"
  ok "Bucket utworzony."

  # Włącz wersjonowanie (ochrona stanu Terraform przed przypadkowym usunięciem)
  gsutil versioning set on "gs://${STATE_BUCKET}"
  ok "Wersjonowanie włączone."

  # Włącz Uniform Bucket-Level Access (bezpieczeństwo)
  gsutil ubla set on "gs://${STATE_BUCKET}"
  ok "Uniform Bucket-Level Access włączony."
fi

# ── 6. Uwierzytelnienie Application Default Credentials ─────────────────────
log "Konfigurowanie Application Default Credentials dla Terraform..."
gcloud auth application-default login
ok "ADC skonfigurowane."

# ── 7. Podsumowanie i instrukcje ─────────────────────────────────────────────
echo ""
echo -e "${BOLD}══════════════════════════════════════════════${RESET}"
echo -e "${GREEN}${BOLD}   Bootstrap zakończony pomyślnie!           ${RESET}"
echo -e "${BOLD}══════════════════════════════════════════════${RESET}"
echo ""
echo -e "${BOLD}Następne kroki:${RESET}"
echo ""
echo -e "${BOLD}1. Odblokuj backend GCS w terraform/stage/main.tf:${RESET}"
echo "   Zamień zakomentowany blok backend \"gcs\" i wpisz:"
echo "     bucket = \"${STATE_BUCKET}\""
echo "     prefix = \"terraform/stage\""
echo ""
echo -e "${BOLD}2. Uzupełnij zmienne Terraform:${RESET}"
echo "   cp terraform/stage/terraform.tfvars.example terraform/stage/terraform.tfvars"
echo "   # Edytuj plik terraform.tfvars – wpisz swoje dane"
echo ""
echo -e "${BOLD}3. Zainicjuj Terraform:${RESET}"
echo "   cd terraform/stage"
echo "   terraform init"
echo ""
echo -e "${BOLD}4. Sprawdź plan:${RESET}"
echo "   terraform plan"
echo ""
echo -e "${BOLD}5. Zastosuj konfigurację:${RESET}"
echo "   terraform apply"
echo ""
echo -e "${BOLD}6. Po apply – dodaj rekord DNS:${RESET}"
echo "   terraform output lb_ip"
echo "   # W panelu DNS dodaj rekord A dla swojej domeny:"
echo "   # app.example.com → <lb_ip>"
echo ""
echo -e "${BOLD}7. Poczekaj na certyfikat SSL (10-30 min):${RESET}"
echo "   # Google automatycznie wyda certyfikat po weryfikacji DNS"
echo "   # Sprawdź status: gcloud compute ssl-certificates list"
echo ""
echo -e "${YELLOW}WAŻNE: Plik terraform.tfvars zawiera sekretne dane – NIE dodawaj go do git!${RESET}"
echo "   (jest już w .gitignore)"
